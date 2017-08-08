#!/usr/bin/env python
# encoding: utf-8

import base64
import json
import logging
import time

from comm import tmtool
from comm.lru import LRU
from douban_config import CrawlerConfig, SDSConfig, LCSConfig, IntervalConfig, Reporter
from douban_contants import TaskTag
from douban_page_parser import TopicPageParser
from douban_statistics import DoubanStatistics
from gen_chatbot_data import ChatbotDoubanGroupStruct, ChatbotDoubanGroupPage
from helper.lcs_helper import LCSAgentClient
from helper.sds_helper import SDSHelper
from micrawler.micrawler_client import MiCrawlerClient
from micrawler.micrawler_consumer import MiCrawlerConsumer
from sds_douban_meta import SDSDoubanMeta

logger = logging.getLogger(__name__)
Reporter.run()


class DoubanUrl(object):
    base_url = 'https://www.douban.com/group/topic'

    @staticmethod
    def build_url(topic, start=0):
        return '%s/%s/?start=%s' % (DoubanUrl.base_url, topic, start)

    @staticmethod
    def url_topic_id(url):
        try:
            topic_id = int(url.split('/')[-2])
        except:
            topic_id = -1
        return topic_id

    @staticmethod
    def url_start(url):
        return int(url.split('=')[-1])

    @staticmethod
    def topic_rest_pages(url, page_info):
        topic = DoubanUrl.url_topic_id(url)

        if page_info['this_page'] != 1 or page_info['total_page'] == 1:
            return None
        links = [DoubanUrl.build_url(topic, x*100) for x in range(1, page_info['total_page'])]
        links = links[: 4]
        return links


class ClusterDouban(object):
    def __init__(self):
        pass

    def put_crawl_result(self, crawl_result):
        pass

    def put_struct_result(self, struct_result):
        pass

    def put2cluster(self, crawl_result, struct_result):
        pass


class LCSDouban(ClusterDouban):
    def __init__(self):
        super(LCSDouban, self).__init__()
        self._cluster_name = LCSConfig.cluster_name
        self._org_id = LCSConfig.org_id
        self._topic_name_page = LCSConfig.topic_name_douban_page
        self._topic_name_struct = LCSConfig.topic_name_douban_struct
        self._topic_name_merged_struct = LCSConfig.topic_name_douban_merged_struct
        self._team_id = LCSConfig.team_id
        self._lcs = LCSAgentClient(self._cluster_name, self._org_id, team_id=self._team_id)

    def put_crawl_result(self, crawl_result):
        url = crawl_result.get('url')
        source_record = ChatbotDoubanGroupPage(
            url=url,
            rawData=crawl_result.get('rawData'),
            fetchTime=crawl_result.get('fetchTime'),
            taskTag=crawl_result.get('taskTag'),
            linkinfo=crawl_result.get('linkInfo', ''),
            fdsPath=crawl_result.get('fdsPath', ''),
        )
        logger.debug('Put source to hdfs for: %s' % url)
        self._lcs.serialize_put(source_record, topic_name=self._topic_name_page)

    def _struct_record(self, struct_result):
        topic_id = int(struct_result.get('topic_id'))
        this_page = int(struct_result['page_info']['this_page'])
        total_page = int(struct_result['page_info']['total_page'])
        url = DoubanUrl.build_url(topic_id, 100 * (this_page-1))
        now = tmtool.now_ts()
        struct_record = ChatbotDoubanGroupStruct(
            topicId=topic_id,
            url=url,
            updateTime=now,
            rawData=json.dumps(struct_result),
            thisPage=this_page,
            totalPage=total_page
        )
        return struct_record

    def put_struct_result(self, struct_result):
        struct_record = self._struct_record(struct_result)
        logger.debug('Put struct to hdfs for: %s' % struct_record.url)
        self._lcs.serialize_put(struct_record, topic_name=self._topic_name_struct)

    def put_merged_struct_result(self, struct_result):
        struct_record = self._struct_record(struct_result)
        self._lcs.serialize_put(struct_record, topic_name=self._topic_name_merged_struct)

    def put2cluster(self, crawl_result, struct_result):
        self.put_crawl_result(crawl_result)
        self.put_struct_result(struct_result)


class SDSDouban(ClusterDouban):
    def __init__(self):
        super(SDSDouban, self).__init__()
        self._app_key = SDSConfig.chatbot_app_key
        self._app_secret = SDSConfig.chatbot_app_secret
        self._endpoint = SDSConfig.chatbot_sds_endpoint
        self._source_table = SDSConfig.chatbot_source_table_name
        self._struct_table = SDSConfig.chatbot_struct_table_name
        self._sds = SDSHelper(self._app_key, self._app_secret, self._endpoint)

        self.statistics = DoubanStatistics()
        self.statistics.start()

    def _struct_record(self, struct_result):
        topic_id = int(struct_result.get('topic_id'))
        this_page = int(struct_result['page_info']['this_page'])
        total_page = int(struct_result['page_info']['total_page'])
        url = DoubanUrl.build_url(topic_id, 100 * (this_page-1))
        task_tag = TaskTag.DOUBAN_COMMENT_PAGE if this_page > 1 else TaskTag.DOUBAN_INDEX_PAGE
        now = tmtool.now_ts()
        today = tmtool.today_ds()

        struct_record = dict(
            date=today,
            topicId=topic_id,
            thisPage=this_page,
            totalPage=total_page,
            taskTag=task_tag,
            updateTime=now,
            rawData=base64.b64encode(json.dumps(struct_result)),
            url=url
        )

        return struct_record

    def put_struct_result(self, struct_result):
        r = self._struct_record(struct_result)
        logger.debug('Put struct to sds for: %s %s %s' % (r['today'], r['topic_id'], r['this_page']))
        self._sds.put(self._struct_table, r)
        self.statistics.record(self._struct_table, 1)

    def put_struct_results(self, struct_results):
        rs = map(lambda x: self._struct_record(x), struct_results)
        logger.debug('Put batch struct to sds for count: %s ' % len(rs))
        self._sds.batch_put(self._struct_table, rs)
        self.statistics.record(self._struct_table, len(rs))

    def put2cluster(self, crawl_result, struct_result):
        url = crawl_result.get('url')
        topic_id = DoubanUrl.url_topic_id(url)
        this_page = struct_result['page_info']['this_page']
        total_page = struct_result['page_info']['total_page']
        task_tag = crawl_result['taskTag']
        now = tmtool.now_ts()
        today = tmtool.today_ds()

        source_record = dict(
            date=today,
            topicId=topic_id,
            thisPage=this_page,
            totalPage=total_page,
            taskTag=task_tag,
            fetchTime=crawl_result.get('fetchTime'),
            rawData=buffer(crawl_result.get('rawData')),
            url=url
        )

        struct_record = dict(
            date=today,
            topicId=topic_id,
            thisPage=this_page,
            totalPage=total_page,
            taskTag=task_tag,
            updateTime=now,
            rawData=base64.b64encode(json.dumps(struct_result)),
            url=url
        )

        logger.debug('Put source and struct to sds for: %s %s %s' % (today, topic_id, this_page))
        # self._sds.put(self._source_table, source_record)
        self._sds.put(self._struct_table, struct_record)

        # self.statistics.record(self._source_table, 1)
        self.statistics.record(self._struct_table, 1)


class DoubanCrawlerConsumer(MiCrawlerConsumer):
    crawled_submit_interval = 10

    def __init__(self, env, topic, group_id, sds_crawler_table_name, put2sds=True, put2lcs=False, outfpath=None):
        super(DoubanCrawlerConsumer, self).__init__(env, topic, group_id, sds_crawler_table_name)
        self._crawler_client = MiCrawlerClient(CrawlerConfig.service_env, CrawlerConfig.business_name)
        self._sds_douban_meta = SDSDoubanMeta()
        self._put2sds = put2sds
        self._put2lcs = put2lcs
        if put2sds:
            self._sds_douban = SDSDouban()
        if put2lcs:
            self._lcs_douban = LCSDouban()
        self._crawled_index_page_count = 0
        self._crawled_max_topic_id = 0

        self._retry_cache = LRU(50000)
        self._retry_limit = 3

        if outfpath is not None:
            self._outf = open(outfpath, 'a')
        else:
            self._outf = None

    def put2cluster(self, crawl_result, struct_result):
        if self._outf is not None:
            self._outf.write('%s\n' % json.dumps(struct_result))

        if self._put2sds:
            self._sds_douban.put2cluster(crawl_result, struct_result)
        if self._put2lcs:
            self._lcs_douban.put2cluster(crawl_result, struct_result)

    def want_upate_crawled_topic_id(self, topic_id):
        self._crawled_max_topic_id = max(self._crawled_max_topic_id, topic_id)
        self._crawled_index_page_count += 1
        if self._crawled_index_page_count % self.crawled_submit_interval == 0:
            logger.debug('Update crawled topic %s' % topic_id)
            self._sds_douban_meta.condition_update_crawled_topic_id(topic_id)

    def condition(self, msg):
        Reporter.pc.count(Reporter.build_name('crawler_msg'))

        url = msg.get('url')
        topic_id = DoubanUrl.url_topic_id(url)
        status_code = msg.get('httpStatusCode')
        exception = msg.get('exceptionDesc', 'No ExceptionDesc Field')
        logger.info('Received micrawler msg status code %s for topic %s' % (status_code, topic_id))

        Reporter.pc.count(Reporter.build_name('crawler_msg_status_%s' % status_code))

        if status_code == 200 and exception is None:
            Reporter.pc.count(Reporter.build_name('crawler_msg_valid'))
            return True

        if status_code == 403 and self._retry_cache.get(url) < self._retry_limit:
            logger.info('Receive 403 for topic %s, retry' % topic_id)
            try:
                self._crawler_client.submit_tasks([url], msg.get('taskTag'))
            except Exception as e:
                Reporter.pc.count(Reporter.build_name('crawler_msg_internal_exception'))
                logger.exception(e)
            self._retry_cache.incr(url, 1)

        try:
            self.want_upate_crawled_topic_id(topic_id)
        except exception as e:
            Reporter.pc.count(Reporter.build_name('crawler_msg_internal_exception'))
            logger.exception(e)

        Reporter.pc.count(Reporter.build_name('crawler_msg_invalid'))
        return False

    def action(self, msg, crawl_result):
        # !!! UGLY !!!
        # todo: 使用更细粒度的 exception，单独控制
        try:
            Reporter.pc.count(Reporter.build_name('crawler_source'))

            url = crawl_result.get('url')
            task_tag = crawl_result.get('taskTag')
            raw_data = crawl_result.get('rawData')
            fds_path = crawl_result.get('fdsPath')

            Reporter.pc.count(Reporter.build_name('crawler_source_task_tag_%s' % task_tag))

            logger.info('Start dealing with: %s' % url)
            logger.debug(msg)

            if url is None or raw_data is None or task_tag is None:
                logger.warn('Not enough info in crawled raw data')
                return

            if fds_path is not None:
                logger.warn('Crawled raw data stored in fds, ignoring')
                return

            topic_id = DoubanUrl.url_topic_id(url)
            struct_result = TopicPageParser(raw_data).parse()
            if struct_result is None:
                Reporter.pc.count(Reporter.build_name('crawler_source_invalid'))
                logger.warn('Can not parse raw data for: %s with length %d' % (topic_id, len(raw_data)))
                if 250 < len(raw_data) < 300 and self._retry_cache.get(url) < self._retry_limit:
                    logger.warn('May be js script, retry for %s' % topic_id)
                    self._crawler_client.submit_tasks([url], task_tag)
                    self._retry_cache.incr(url, 1)
                    Reporter.pc.count(Reporter.build_name('crawler_retry'))
                return

            if task_tag == TaskTag.DOUBAN_INDEX_PAGE:
                self.want_upate_crawled_topic_id(topic_id)

                rest_pages = DoubanUrl.topic_rest_pages(url, struct_result['page_info'])
                if rest_pages is not None:
                    logger.debug('Submit %s comment pages for topic %s' % (len(rest_pages), topic_id))
                    self._crawler_client.submit_tasks(rest_pages, TaskTag.DOUBAN_COMMENT_PAGE)
                    Reporter.pc.count(Reporter.build_name('crawler_source_comment_submit'))

            time.sleep(IntervalConfig.crawl_interlval)
            self.put2cluster(crawl_result, struct_result)
        except Exception as e:
            Reporter.pc.count(Reporter.build_name('crawler_action_internal_exception'))
            logger.exception(e)

    def run(self):
        def report_live():
            Reporter.pc.set_gauge(Reporter.build_name('live_crawler_consumer'), 1)
        tmtool.periodic_threading(1)(report_live)()

        super(DoubanCrawlerConsumer, self).run()


def main():
    consumer = DoubanCrawlerConsumer(CrawlerConfig.service_env, CrawlerConfig.kafaka_topic,
                                     CrawlerConfig.kafka_group_id, CrawlerConfig.crawler_table_name,
                                     True, True)
                                     # False, False, '/home/efei/data/douban_crawler_consumer_source_and_struct.txt')
    consumer.run()


if __name__ == '__main__':
    main()
