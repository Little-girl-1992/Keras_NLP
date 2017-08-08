#!/usr/bin/env python
# encoding: utf-8


import time

from douban.douban_config import SDSConfig
from helper.sds_helper import SDSHelper


class SDSDoubanMeta(object):
    def __init__(self):
        self.meta_table_name = SDSConfig.chatbot_meta_table_name
        self.sds = SDSHelper(SDSConfig.chatbot_app_key, SDSConfig.chatbot_app_secret)

    @staticmethod
    def now():
        return int(time.time() * 1000)

    def get_topic_id(self, topic_type):
        res = self.sds.get(self.meta_table_name, {'topicType': topic_type})
        return res['topicId']

    def update_topic_id(self, topic_type, topic_id):
        self.sds.put(
            self.meta_table_name,
            {'topicType': topic_type, 'topicId': topic_id, 'updateTime': self.now()}
        )

    def condition_update_crawled_topic_id(self, topic_id):
        crawled_topic_id = self.get_topic_id('crawled')
        if topic_id > crawled_topic_id:
            self.update_topic_id('crawled', topic_id)
