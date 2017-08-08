#!/usr/bin/env python
# encoding: utf-8

import json
import time
import logging

from helper.kafka_helper import Consumer
from helper.sds_helper import SDSHelper

logger = logging.getLogger(__name__)


kafka_configs = dict(
    STAGING=dict(
        zookeeper='zk1.staging.srv:2181,zk2.staging.srv:2181,zk3.staging.srv:2181,zk4.staging.srv:2181,zk5.staging.srv:2181/kafka-misearch-zc',
        brokers='tj1-vm-search001.kscn:9092,tj1-vm-search003.kscn:9092,tj1-vm-search005.kscn:9092',
    ),
    C3=dict(
        zookeeper='c3-hadoop-srv-ct06.bj:11000,c3-hadoop-srv-ct07.bj:11000,c3-hadoop-srv-ct08.bj:11000,c3-hadoop-srv-ct09.bj:11000,c3-hadoop-srv-ct10.bj:11000/kafka/misearch',
        brokers='c3-s-search01.bj:9092,c3-s-search03.bj:9092,c3-s-search05.bj:9092',
    )
)

sds_configs = dict(
   STAGING=dict(
        endpoint='http://cnbj1-sds.api.xiaomi.net',
        app_key='AK5KLGCCWTYNH77WDR',
        app_secret='effFrnEy02J4xsGcbqG1MBd+FFkuvrdMgcHR4GI+',
    ),
    C3=dict(
        endpoint='http://cnbj1-sds.api.xiaomi.net',
        app_key='AK5KLGCCWTYNH77WDR',
        app_secret='effFrnEy02J4xsGcbqG1MBd+FFkuvrdMgcHR4GI+',
    )
)


class MiCrawlerConsumer(object):
    def __init__(self, env, topic, group_id, sds_table_name):
        self._env = env
        self._kafka_brokers = kafka_configs[self._env]['brokers']
        self._kafka_group_id = group_id
        self._kafka_topic = topic
        self._sds_table_name = sds_table_name
        self._sds_endpoint = sds_configs[self._env]['endpoint']
        self._sds_app_key = sds_configs[self._env]['app_key']
        self._sds_app_secret = sds_configs[self._env]['app_secret']

        self.kafka_consumer = Consumer(topic, broker_servers=self._kafka_brokers, group_id=self._kafka_group_id).get()
        self.sds_client = SDSHelper(self._sds_app_key, self._sds_app_secret, self._sds_endpoint)

    def get_content_from_sds(self, task_tag, hash_code):
        res = self.sds_client.get(
            self._sds_table_name,
            {'taskTag': task_tag, 'hashCode': hash_code}
        )
        return res

    # 需要重写
    def condition(self, msg):
        logger.info('Judge if pull sds content for: %s_%s' % (msg['taskTag'], msg['hashCode']))
        return True

    # 需要重写
    def action(self, msg, res):
        logger.info('Deal with received crawled result for %s_%s' % (res['taskTag'], res['hashCode']))

    def run(self):
        logger.debug('Start consumer micrawler result')
        last_ts = int(time.time())

        for msg in self.kafka_consumer:
            logger.debug(msg)

            now_ts = time.time()
            if now_ts - last_ts > 1:
                self.kafka_consumer.commit()
                last_ts = now_ts

            try:
                msg = json.loads(msg.value)
            except Exception as e:
                logger.warn('Json loads error for kafka msg.value')
                logger.exception(e)
                continue
            if self.condition(msg):
                try:
                    res = self.get_content_from_sds(msg['taskTag'], msg['hashCode'])
                except Exception as e:
                    logger.exception(e)
                    continue
                else:
                    if res is not None:
                        self.action(msg, res)


if __name__ == '__main__':
    from douban.douban_config import CrawlerConfig

    consumer = MiCrawlerConsumer(CrawlerConfig.service_env, CrawlerConfig.kafaka_topic, CrawlerConfig.kafka_group_id,
                                 CrawlerConfig.crawler_table_name)
    consumer.run()
