#!/usr/bin/env python
# encoding: utf-8

import os
import logging

fmt = "[%(levelname)1.1s] [%(asctime)s %(module)s:%(lineno)d] %(message)s"
logging.basicConfig(level=logging.INFO, format=fmt)
logger = logging.getLogger(__file__)


class IntervalConfig(object):
    crawl_interlval = 0.02
    scan_interval = 0.003


class SDSConfig(object):
    chatbot_app_key = 'AKJ5M6PHCYL6ZUTSZ6'
    chatbot_app_secret = 'hnODlmJO7gOmk7VGgmE//h5HDaWoAPTQibDb2KBI'
    chatbot_convs_table_name = 'CL5035/hw_weibo_conv'
    chatbot_convs_clean_table_name = 'CL5035/hw_weibo_conv_clean'
    chatbot_statistic_table_name = 'CL5035/crawl_statistics'
    chatbot_sds_endpoint = 'http://cnbj1-sds.api.xiaomi.net'
