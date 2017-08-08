#!/usr/bin/env python
# encoding: utf-8

import time
import logging

from comm import tmtool, clean, script
from weibo.weibo_config import SDSConfig, IntervalConfig
from weibo.weibo_statistics import WeiboStatistics
from weibo.weibo_clean import clean_conv
from helper.sds_helper import SDSHelper


logger = logging.getLogger(__file__)
sds = SDSHelper(SDSConfig.chatbot_app_key, SDSConfig.chatbot_app_secret, SDSConfig.chatbot_sds_endpoint)
statistics = WeiboStatistics()


def clean_convs_in_sds(start_dt_s, stop_dt_s):
    statistics.start()

    start_update_time = tmtool.datetime_str_2_ts(start_dt_s)
    stop_update_time = tmtool.datetime_str_2_ts(stop_dt_s)

    for sds_record in sds.scan_multi(SDSConfig.chatbot_convs_table_name,
                                     start_key={'updateTime': start_update_time},
                                     stop_key={'updateTime': stop_update_time},
                                     indexName='update_time_index'):
        conv = [sds_record.get('post', ''), sds_record.get('resp', '')]
        cleaned_conv = clean_conv(conv)
        if cleaned_conv is not None:
            logger.info(clean.joint_conv_str(cleaned_conv))
            sds.put(SDSConfig.chatbot_convs_clean_table_name, dict(
                post=cleaned_conv[0],
                resp=cleaned_conv[1],
                updateTime=tmtool.now_ts(),
                source='hw_weibo'
            ))
            statistics.record(SDSConfig.chatbot_convs_clean_table_name, 1)

        time.sleep(IntervalConfig.scan_interval)

    statistics.flush()
    statistics.stop()


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-c', '--clean', action='store_true', default=False, help='clean in sds')
    parser.add_argument('--start', default='2017-07-10 00:00:00', help='start time')
    parser.add_argument('--stop', default='2017-07-20 00:00:00', help='stop time')
    parser.add_argument('-p', '--putFile', action='store_true', default=False, help='put file convs to sds')
    parser.add_argument('--filePath', help='file path for put file convs to sds')
    parser.add_argument('--source', default=None, help='if use source for put file convs to sds')

    args = parser.parse_args()

    if args.clean:
        clean_convs_in_sds(args.start, args.stop)
    elif args.putFile:
        if args.source is not None:
            table_name = SDSConfig.chatbot_convs_clean_table_name
        else:
            table_name = SDSConfig.chatbot_convs_table_name
        script.convs_to_sds_from_file(args.filePath, table_name, args.source)
    else:
        parser.print_help()
