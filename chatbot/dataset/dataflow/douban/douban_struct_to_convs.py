#!/usr/bin/env python
# encoding: utf-8

import base64
import logging
import time
import datetime
import multiprocessing
from Queue import Queue
import ujson as json
from collections import defaultdict

from comm import tmtool, clean
from douban_config import SDSConfig, IntervalConfig, ENV
from douban_statistics import DoubanStatistics
from douban_clean import clean_conv
from helper.sds_helper import SDSHelper
from xiaomi_py_perfcounter import ClusterPerfCounter
from douban_crawler_consumer import LCSDouban
from douban_extract_conv import merge_records, extract_title_comments, replace_line_break, out_encode

logger = logging.getLogger(__file__)

sds = SDSHelper(SDSConfig.chatbot_app_key, SDSConfig.chatbot_app_secret, SDSConfig.chatbot_sds_endpoint)
lcs = LCSDouban()

statistics = DoubanStatistics()


# 用以临时存储batch put的record
class BatchRecords(object):
    limit = 20
    records = defaultdict(list)

    @staticmethod
    def put(table):
        try:
            sds.batch_put(table, BatchRecords.records[table])
        except Exception as e:
            logger.exception(e)
        BatchRecords.records[table] = []


    @staticmethod
    def append(table, rs):
        BatchRecords.records[table] += rs
        if len(BatchRecords.records[table]) >= BatchRecords.limit:
            BatchRecords.put(table)

    @staticmethod
    def flush():
        for table in BatchRecords.records.iterkeys():
            BatchRecords.put(table)


class Reporter(object):
    metrics_queue = multiprocessing.Queue(maxsize=10000)

    pc = ClusterPerfCounter(metrics_queue, worker_name_flag='IS_WORKER')
    running = False

    @staticmethod
    def run():
        if not Reporter.running:
            Reporter.pc.run()
            Reporter.running = True

    @staticmethod
    def build_name(x):
        return '%s.dlchatbot_dataflow_douban.%s' % (ENV, x)


def hash_conv(conv):
    s = clean.joint_conv_str(conv)
    return tmtool.md5(s)


def complete_records(records):
    record = merge_records(records)
    if record is None or 'topic' not in record:
        Reporter.pc.count(Reporter.build_name('struct_merged_invalid'))
        return

    logger.info('Put merged struct to hdfs for topic: %s' % record['topic_id'])
    lcs.put_merged_struct_result(record)

    convs = extract_title_comments(record)
    rs = map(lambda conv: dict(
        post=out_encode(conv[0]),
        resp=out_encode(conv[1]),
        updateTime=tmtool.now_ts()
    ), convs)
    BatchRecords.append(SDSConfig.chatbot_convs_table_name, rs)
    logger.info('Put %s convs to sds for topic: %s' % (len(convs),  record['topic_id']))

    cleaned_convs = map(lambda x: clean_conv(x), convs)
    cleaned_convs = filter(lambda x: x is not None, cleaned_convs)
    rs = map(lambda conv: dict(
        post=out_encode(conv[0]),
        resp=out_encode(conv[1]),
        updateTime=tmtool.now_ts(),
        source='douban'
    ), cleaned_convs)
    BatchRecords.append(SDSConfig.chatbot_convs_clean_table_name, rs)
    logger.info('Put %s cleaned convs to sds for topic: %s' % (len(cleaned_convs),  record['topic_id']))

    statistics.record(SDSConfig.chatbot_convs_table_name, len(convs))
    statistics.record(SDSConfig.chatbot_convs_clean_table_name, len(cleaned_convs))
    Reporter.pc.count(Reporter.build_name('struct_merged'))
    Reporter.pc.count(Reporter.build_name('conv'), len(convs))
    Reporter.pc.count(Reporter.build_name('conv_clean'), len(cleaned_convs))


def run_for_iterators(it):
    last_topic = None
    records = []
    time.sleep(IntervalConfig.scan_interval)
    for sds_record in it:
        # !!! UGLY !!!
        # todo: 使用更细粒度的 exception 控制
        try:
            Reporter.pc.count(Reporter.build_name('struct'))
            record = sds_record['rawData']
            record = json.loads(base64.b64decode(record))
            curr_topic = sds_record['topicId']
            if curr_topic == last_topic:
                records.append(record)
            else:
                complete_records(records)
                records = [record]
                time.sleep(IntervalConfig.scan_interval)
            last_topic = curr_topic
        except Exception as e:
            logger.exception(e)
            Reporter.pc.mark_meter('struct_internal_exception')
            continue
    BatchRecords.flush()
    statistics.flush()


def run_one_day(date):
    logger.info('>>>>> Start convert for date: %s on %s <<<<<' % (date, tmtool.now_fmt()))
    statistics.start()

    # # 单线程
    # it = sds.scan_multi(SDSConfig.chatbot_struct_table_name, start_key={'date': date}, stop_key={'date': date})
    # run_for_iterators(it)

    # 多线程
    scan_table_splits = sds.scan_multi(SDSConfig.chatbot_struct_table_name,
                                    start_key={'date': date}, stop_key={'date': date},
                                    one_iterator=False, use_table_splits=True)
    task_queue = multiprocessing.Queue()
    for tp in scan_table_splits:
        task_queue.put(tp)

    # @tmtool.func_threading(daemon=True)
    @tmtool.func_processing(daemon=True, name_prefix='IS_WORKER')
    def worker(tid=0):
        Reporter.run()
        pid = multiprocessing.current_process().pid
        while True:
            if task_queue.empty():
                return
            tp = task_queue.get()
            it = sds.scan(SDSConfig.chatbot_struct_table_name, tp.startKey, tp.stopKey, inGlobalOrder=False)
            logger.info('Worker %s start consume new table split' % pid)
            logger.info('Worker %s table split: %s' % (pid, tp))
            run_for_iterators(it)
            logger.info('Worker %s has consumed one table split' % pid)
            # task_queue.task_done()

    ts = [worker(i) for i in range(10)]
    Reporter.run()
    # task_queue.join()
    for t in ts:
        t.join()

    statistics.flush()
    statistics.stop()
    logger.info('>>>>> Complete convert for date: %s on %s <<<<<' % (date, tmtool.now_fmt()))


def run_yesterday():
    logger.info('>>>>> Run for yesterday struct to convs <<<<<')
    today = tmtool.today_ds()
    date = today - 1
    if statistics.check_table_row(today, SDSConfig.chatbot_convs_table_name):
        logger.info('>>>>> Convs table existed for date: %s, skip <<<<<' % date)
    else:
        run_one_day(date)


def next_sched_time(sched_time_s):
    s = datetime.datetime.strptime(sched_time_s, tmtool.time_fmt)
    n = datetime.datetime.now()
    t = n + datetime.timedelta(days=1)
    today_time = datetime.datetime(n.year, n.month, n.day, s.hour, s.minute, s.second)
    tomor_time = datetime.datetime(t.year, t.month, t.day, s.hour, s.minute, s.second)

    if n < today_time:
        sched_time = today_time
    else:
        sched_time = tomor_time

    return sched_time


def main(sched_time_s='00:00:05'):
    def report_live():
        Reporter.pc.set_gauge(Reporter.build_name('live_struct_to_convs'), 1)
    tmtool.periodic_threading(1)(report_live)()

    run_yesterday()
    next_at = next_sched_time(sched_time_s)
    rest_seconds = (next_at - datetime.datetime.now()).total_seconds()
    logger.info('>>>>> Will run in %s after %s seconds <<<<<' % (next_at.strftime(tmtool.datetime_fmt), rest_seconds))
    while True:
        if datetime.datetime.now() > next_at:
            run_yesterday()
            next_at = next_sched_time(sched_time_s)
            rest_seconds = (next_at - datetime.datetime.now()).total_seconds()
            logger.info('>>>>> Will run in %s after %s seconds <<<<<' % (next_at.strftime(tmtool.datetime_fmt), rest_seconds))
        time.sleep(1)


if __name__ == '__main__':
    main()
    # run_one_day(tmtool.today_ds() - 2)
