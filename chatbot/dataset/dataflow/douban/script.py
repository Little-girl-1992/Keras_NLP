#!/usr/bin/env python
# encoding: utf-8

import time
import logging
import Queue
import ujson as json

from threading import Thread
from comm import tmtool, clean
from comm.detect import Detection
from douban_crawler_consumer import LCSDouban, SDSDouban
from douban_config import SDSConfig, IntervalConfig
from douban_statistics import DoubanStatistics
from douban_clean import clean_conv
from helper.sds_helper import SDSHelper
from gen_chatbot_data import ChatbotDoubanGroupStruct, ChatbotDoubanGroupPage


logger = logging.getLogger(__file__)
sds = SDSHelper(SDSConfig.chatbot_app_key, SDSConfig.chatbot_app_secret, SDSConfig.chatbot_sds_endpoint)
statistics = DoubanStatistics()


def clean_convs_in_sds(start_dt_s, stop_dt_s):
    statistics.start()

    start_update_time = tmtool.datetime_str_2_ts(start_dt_s)
    stop_update_time = tmtool.datetime_str_2_ts(stop_dt_s)

    for sds_record in sds.scan_multi_index(
            SDSConfig.chatbot_convs_table_name,
            index_name='update_time_index',
            start_key={'updateTime': start_update_time},
            stop_key={'updateTime': stop_update_time}
    ):

        conv = [sds_record.get('post', ''), sds_record.get('resp', '')]
        cleaned_conv = clean_conv(conv)
        if cleaned_conv is not None:
            logger.info(clean.joint_conv_str(cleaned_conv))
            sds.put(SDSConfig.chatbot_convs_clean_table_name, dict(
                post=cleaned_conv[0],
                resp=cleaned_conv[1],
                updateTime=tmtool.now_ts(),
                source='douban'
            ))
            statistics.record(SDSConfig.chatbot_convs_clean_table_name, 1)

        time.sleep(IntervalConfig.scan_interval / 2.0)

    statistics.flush()
    statistics.stop()


def count(table_name=None, start_dt_s=None, stop_dt_s=None):
    if start_dt_s is None:
        start_key = None
    else:
        start_update_time = tmtool.datetime_str_2_ts(start_dt_s)
        start_key = {'updateTime': start_update_time}
    if stop_dt_s is None:
        stop_key = None
    else:
        stop_update_time = tmtool.datetime_str_2_ts(stop_dt_s)
        stop_key = {'updateTime': stop_update_time}

    if table_name is None:
        table_name = SDSConfig.chatbot_convs_table_name

    logger.info('Count for %s' % table_name)

    scan_iterators = sds.scan_multi_index(table_name, 'update_time_index', start_key, stop_key, False,
                                          attributes=['updateTime'])
    task_queue = Queue.Queue()
    for it in scan_iterators:
        task_queue.put(it)

    results = []

    @tmtool.func_threading(daemon=True)
    def worker(tid):
        while True:
            if task_queue.empty():
                return
            count = 0
            it = task_queue.get()
            for _ in it:
                count += 1
                if count % 1000 == 0:
                    logger.info('worker %s count %s' % (tid, count))
                time.sleep(0.001)
            logger.info(count)
            results.append(count)
            task_queue.task_done()

    ts = [worker(i) for i in range(10)]
    task_queue.join()

    total_count = sum(results)

    logger.info(results)
    logger.info('Total count %s' % total_count)


def struct_to_cluster_from_file(inpath):
    task_queue = Queue.Queue(maxsize=10000)
    count_interval = 1000

    @tmtool.func_threading(daemon=True)
    def producer(tid):
        count = 0
        with open(inpath) as f:
            for line in f:
                count += 1
                # 略过已处理的
                # if count < 800000:
                #     continue
                task_queue.put(line)
                if count % count_interval == 0:
                    logger.info('Producer %s has produce %s' % (tid, count))
            logger.info('Has produce %s' % count)

    @tmtool.func_threading(daemon=True)
    def worker(tid):
        lcs = LCSDouban()
        sds = SDSDouban()
        count = 0
        batch_rs = []
        while True:
            try:
                r = task_queue.get(timeout=10)
            except:
                logger.info('Has Wait for 10s')
                logger.info('Worker %s has consume %s' % (tid, count))
                return
            # 略过过长的
            if len(r) > 1024*1024:
                continue
            try:
                r = json.loads(r)
            except:
                continue

            count += 1
            lcs.put_struct_result(r)
            batch_rs.append(r)
            if len(batch_rs) >= 40:
                try:
                    sds.put_struct_results(batch_rs)
                except Exception as e:
                    logger.exception(e)
                batch_rs = []
            if count % count_interval == 0:
                logger.info('Worker %s has consume %s' % (tid, count))
            task_queue.task_done()
            time.sleep(0.001)
            # time.sleep(1)

    pt = producer(0)
    ts = [worker(i) for i in range(20)]
    time.sleep(10)
    task_queue.join()


if __name__ == '__main__':
    import sys
    # clean_convs_in_sds('2017-07-13 00:00:00', '2017-07-14 00:00:00')
    # count()
    struct_to_cluster_from_file(sys.argv[1])
