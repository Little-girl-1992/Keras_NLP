#!/usr/bin/env python
# encoding: utf-8


import logging

from comm import statistics
from weibo.weibo_config import SDSConfig

logger = logging.getLogger(__name__)


class WeiboStatistics(statistics.Statistics):
    def __init__(self, update_interval=60, statistic_table_name=SDSConfig.chatbot_statistic_table_name,
                 app_key=SDSConfig.chatbot_app_key, app_secret=SDSConfig.chatbot_app_secret):
        super(WeiboStatistics, self).__init__(update_interval, statistic_table_name, app_key, app_secret)
