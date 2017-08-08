#!/usr/bin/env python
# encoding: utf-8

import logging
import sched
import time

import requests
from retrying import retry

from comm.tmtool import periodic_threading
from douban_config import CrawlerConfig, Reporter
from douban_contants import TaskTag
from micrawler.micrawler_client import MiCrawlerClient
from sds_douban_meta import SDSDoubanMeta

logger = logging.getLogger(__name__)
Reporter.run()


class CrawlScheduler(object):
    latest_topic_url = 'https://api.douban.com/v2/group/blabla/topics'
    page_base_url = 'https://www.douban.com/group/topic'
    submit_alpha = 3

    def __init__(self, submit_gap=100, check_submit_interval=None, check_latest_interval=None):
        self.submit_gap = submit_gap
        self.check_submit_interval = check_submit_interval or 5 * 60
        self.check_latest_interval = check_latest_interval or 24 * 3600
        self.douban_meta = SDSDoubanMeta()
        self.crawler_client = MiCrawlerClient(CrawlerConfig.service_env, CrawlerConfig.business_name)

    def build_index_page_url(self, topic_id):
        return '%s/%s/?start=0' % (self.page_base_url, topic_id)

    @retry(stop_max_attempt_number=3, wait_random_min=1, wait_random_max=2)
    def get_latest_topic_id(self):
        res = requests.get(self.latest_topic_url, timeout=3)
        if res.status_code == 200:
            d = res.json()
            latest_topic_url = d['topics'][0]['share_url']
            latest_topic_id = int(latest_topic_url.strip('/').split('/')[-1])
            return latest_topic_id
        else:
            raise Exception('Reqeust Error <%s>' % res.status_code)

    def submit_crawl_urls(self, start, end):
        urls = [self.build_index_page_url(x) for x in range(start, end + 1)]
        chunk_num = 100
        urls_chunks = [urls[x: x + chunk_num] for x in xrange(0, len(urls), chunk_num)]
        for urls in urls_chunks:
            self.crawler_client.submit_tasks(urls, TaskTag.DOUBAN_INDEX_PAGE)
        self.douban_meta.update_topic_id('submited', end)
        Reporter.pc.set_gauge(Reporter.build_name('crawler_scheduler_latest_add'), len(urls))

    def check_submit(self):
        logger.info('Start check submit from sds douban page meta table')
        latest_id = self.douban_meta.get_topic_id('latest')
        submited_id = self.douban_meta.get_topic_id('submited')
        crawled_id = self.douban_meta.get_topic_id('crawled')
        if submited_id - crawled_id < self.submit_gap:
            logger.info('Index_page urls in crawler not enough, will submit new urls')
            target_id = submited_id + self.submit_alpha * self.submit_gap
            if target_id > latest_id:
                target_id = latest_id
            logger.info('Submit crawl urls topic id %s -> %s' % (submited_id + 1, target_id))
            self.submit_crawl_urls(submited_id + 1, target_id)
            Reporter.pc.count(Reporter.build_name('crawler_scheduler_submit'), self.submit_alpha * self.submit_gap)

    def check_latest(self):
        logger.info('Start check latest from douban group')
        latest_id = self.get_latest_topic_id()
        logger.info('Get latest topic id: %s' % latest_id)
        self.douban_meta.update_topic_id('latest', latest_id)

    def run(self):
        logger.info('Start Crawler Scheduler...')
        # t1 = periodic_threading(self.check_latest_interval)(self.check_latest)()
        t2 = periodic_threading(self.check_submit_interval)(self.check_submit)()
        ts = [t2]
        while True:
            time.sleep(1)
            for t in ts:
                if not t.isAlive():
                    return
            Reporter.pc.set_gauge(Reporter.build_name('live_scheduler'), 1)


if __name__ == '__main__':
    scheduler = CrawlScheduler(500, 10, 24*3600)
    scheduler.run()
