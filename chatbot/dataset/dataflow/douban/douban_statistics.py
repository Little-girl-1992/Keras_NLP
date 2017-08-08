#!/usr/bin/env python
# encoding: utf-8


import copy
import logging

from comm import tmtool, statistics
from collections import defaultdict
from douban.douban_config import SDSConfig
from helper.sds_helper import SDSHelper

logger = logging.getLogger(__name__)


class DoubanStatistics(statistics.Statistics):
    def __init__(self, update_interval=60, statistic_table_name=SDSConfig.chatbot_statistic_table_name,
                 app_key=SDSConfig.chatbot_app_key, app_secret=SDSConfig.chatbot_app_secret):
        super(DoubanStatistics, self).__init__(update_interval, statistic_table_name, app_key, app_secret)
