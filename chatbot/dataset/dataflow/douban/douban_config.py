#!/usr/bin/env python
# encoding: utf-8

import os
import logging
from xiaomi_py_perfcounter import PerfCounter, ClusterPerfCounter

env_name = 'DATAFLOW_DOUBAN_ENV'
if env_name in os.environ:
    ENV = os.environ.get(env_name)
else:
    ENV = 'STAGING'

fmt = "[%(levelname)1.1s] [%(asctime)s %(module)s:%(lineno)d] %(message)s"
log_level = logging.DEBUG if ENV == 'STAGING' else logging.INFO
logging.basicConfig(level=log_level, format=fmt)

logger = logging.getLogger(__file__)
logger.info('>>>>>> Environment is %s <<<<<<' % ENV)


class Reporter(object):
    pc = PerfCounter()
    running = False

    @staticmethod
    def run():
        if not Reporter.running:
            Reporter.pc.run()
            Reporter.running = True

    @staticmethod
    def build_name(x):
        return '%s.dlchatbot_dataflow_douban.%s' % (ENV, x)


class IntervalConfig(object):
    if ENV == 'STAGING':
        crawl_interlval = 1
        scan_interval = 0.1
    else:
        crawl_interlval = 0.02
        scan_interval = 0.001


class SDSConfig(object):
    if ENV == 'STAGING':
        chatbot_app_key = 'AKJ5M6PHCYL6ZUTSZ6'
        chatbot_app_secret = 'hnODlmJO7gOmk7VGgmE//h5HDaWoAPTQibDb2KBI'
        chatbot_meta_table_name = 'CL5035/crawl_douban_meta_staging'
        chatbot_struct_table_name = 'CL5035/crawl_douban_page_struct_staging'
        chatbot_source_table_name = 'CL5035/crawl_douban_page_source_staging'
        chatbot_merge_table_name = 'CL5035/crawl_douban_page_struct_merge_staging'
        chatbot_convs_table_name = 'CL5035/crawl_douban_conv_staging'
        chatbot_convs_clean_table_name = 'CL5035/douban_conv_clean_staging'
        chatbot_statistic_table_name = 'CL5035/crawl_statistics'
        chatbot_sds_endpoint = 'http://cnbj1-sds.api.xiaomi.net'
    else:
        chatbot_app_key = 'AKJ5M6PHCYL6ZUTSZ6'
        chatbot_app_secret = 'hnODlmJO7gOmk7VGgmE//h5HDaWoAPTQibDb2KBI'
        chatbot_meta_table_name = 'CL5035/crawl_douban_meta_c3'
        chatbot_struct_table_name = 'CL5035/crawl_douban_page_struct_c3'
        chatbot_source_table_name = 'CL5035/crawl_douban_page_source_c3'
        chatbot_merge_table_name = 'CL5035/crawl_douban_page_struct_merge_c3'
        chatbot_convs_table_name = 'CL5035/crawl_douban_conv_c3'
        chatbot_convs_clean_table_name = 'CL5035/douban_conv_clean_c3'
        chatbot_statistic_table_name = 'CL5035/crawl_statistics'
        chatbot_sds_endpoint = 'http://cnbj1-sds.api.xiaomi.net'


class CrawlerConfig(object):
    if ENV == 'STAGING':
        service_env = 'STAGING'
        kafaka_topic = 'micrawler_dl_chatbot_douban'
        kafka_group_id = 'dl_chatbot_douban_consumer_staging'
        business_name = 'dl_chatbot_douban'
        crawler_table_name = 'CL3459/globalsearch_rawdata_staging'
    else:
        service_env = 'C3'
        kafaka_topic = 'micrawler_dl_chatbot_douban'
        kafka_group_id = 'dl_chatbot_douban_consumer_c3'
        business_name = 'dl_chatbot_douban'
        crawler_table_name = 'CL3459/globalsearch_rawdata_c3'


class LCSConfig(object):
    cluster_name = 'cnbj1-talos'
    org_id = 'CL5035'
    team_id = 'CI5039'
    topic_name_douban_page = 'micloud_chatbot_douban_group_page'
    topic_name_douban_struct = 'micloud_chatbot_douban_group_struct'
    topic_name_douban_merged_struct = 'micloud_chatbot_douban_group_merged_struct'
