#!/usr/bin/env python
# encoding: utf-8


from douban_config import SDSConfig
from helper.sds_helper import SDSHelper

sds = SDSHelper(SDSConfig.chatbot_app_key, SDSConfig.chatbot_app_secret)


# !!! 慎用 !!!
def clean_table(table_name):
    print(table_name)
    spec = sds._admin_client.describeTable(table_name)
    sds._admin_client.dropTable(table_name)
    sds._admin_client.createTable(table_name, spec)


def main():
    tables = [
       # 'CL5035/crawl_douban_page_struct_staging',
       # 'CL5035/crawl_douban_page_source_staging',
       # 'CL5035/crawl_douban_page_struct_merge_staging',
       # 'CL5035/crawl_douban_conv_staging',
       # 'CL5035/crawl_douban_page_struct_c3',
       # 'CL5035/crawl_douban_page_source_c3',
       # 'CL5035/crawl_douban_page_struct_merge_c3',
       # 'CL5035/crawl_douban_conv_c3',
       # 'CL5035/douban_conv_clean_c3',
    ]

    for table_name in tables:
        clean_table(table_name)


def create_table_from(old_table, new_table):
    print('%s -> %s' % (old_table, new_table))
    spec = sds._admin_client.describeTable(old_table)
    sds._admin_client.createTable(new_table, spec)


if __name__ == '__main__':
    pass
    # main()
    # create_table_from('CL5035/crawl_douban_conv_c3', 'CL5035/hw_weibo_conv')
    # create_table_from('CL5035/douban_conv_clean_c3', 'CL5035/hw_weibo_conv_clean')
