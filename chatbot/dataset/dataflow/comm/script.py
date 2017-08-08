#!/usr/bin/env python
# encoding: utf-8

import os
import time
import tmtool
import random
import uuid
import logging
from Queue import Queue
from threading import Thread

import clean
from statistics import Statistics
from config import SDSConfig, IntervalConfig
from helper.sds_helper import SDSHelper

logger = logging.getLogger(__file__)
sds = SDSHelper(SDSConfig.chatbot_app_key, SDSConfig.chatbot_app_secret, SDSConfig.chatbot_sds_endpoint)
statistics = Statistics(60, SDSConfig.chatbot_statistic_table_name,
                        SDSConfig.chatbot_app_key, SDSConfig.chatbot_app_secret)


def conv_to_sds(table_name, conv, source=None):
    record = dict(
        post=conv[0],
        resp=conv[1],
        updateTime=tmtool.now_ts()
    )
    if isinstance(source, str):
        record['source'] = source
    sds.put(table_name, record)
    statistics.record(table_name, 1)


def convs_to_sds_from_file(inpath, table_name, source=None):
    queue = Queue(maxsize=10000)

    def worker():
        while True:
            if queue.empty():
                return
            conv = queue.get()
            try:
                conv_to_sds(table_name, conv, source)
            except Exception as e:
                logger.exception(e)
            time.sleep(0.01)

    def producer():
        with open(inpath) as f:
            count = 0
            for line in f:
                try:
                    conv = clean.parse_conv_str(line)
                except:
                    continue
                queue.put(conv)
                count += 1
                if count % 10000 == 0:
                    logger.info('Has enqueued %s' % count)
            print 'Has enqueued %s' % count

    statistics.start()

    pt = Thread(target=producer)
    wts = [Thread(target=worker) for _ in range(40)]

    pt.start()

    for t in wts:
        t.start()

    pt.join()
    for t in wts:
        t.join()

    statistics.flush()
    statistics.stop()


def _conv_time_key(dt_s):
    if dt_s is None:
        key = None
    else:
        update_time = tmtool.datetime_str_2_ts(dt_s)
        key = {'updateTime': update_time}
    return key


def count_conv_fron_sds(table_name=None, start_dt_s=None, stop_dt_s=None):
    start_key = _conv_time_key(start_dt_s)
    stop_key = _conv_time_key(stop_dt_s)

    if table_name is None:
        table_name = SDSConfig.chatbot_convs_table_name

    logger.info('Count for %s' % table_name)

    scan_iterators = sds.scan_multi_index(table_name, 'update_time_index', start_key, stop_key, False,
                                          attributes=['updateTime'])
    task_queue = Queue()
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


def download_conv_from_sds(table_name, outpath, start_dt_s, stop_dt_s):
    start_key = _conv_time_key(start_dt_s)
    stop_key = _conv_time_key(stop_dt_s)

    scan_iterators = sds.scan_multi_index(table_name, 'update_time_index', start_key, stop_key, False)
    task_queue = Queue()
    for i, it in enumerate(scan_iterators):
        task_queue.put([i, it])

    outdir = os.path.join('/tmp/convs_from_sds/', str(uuid.uuid4()))
    os.makedirs(outdir)

    @tmtool.func_threading(daemon=True)
    def worker(tid):
        while True:
            if task_queue.empty():
                return
            i, it = task_queue.get()
            print 'Worker %s start download partition %s' % (tid, i)
            count = 0
            with open(os.path.join(outdir, 'part_%s' % i), 'w') as f:
                for sds_record in it:
                    post = sds_record['post']
                    resp = sds_record['resp']
                    line = '%s |<->| %s' % (post, resp)
                    f.write('%s\n' % line)
                    count += 1
                    if count % 1000 == 0:
                        print 'Worker %s has download partition %s count %s' % (tid, i, count)
                time.sleep(0.001)
            print 'Worker %s has download partition %s count %s' % (tid, i, count)
            task_queue.task_done()

    ts = [worker(i) for i in range(20)]
    task_queue.join()

    print 'Start cat all to one file'
    os.system('cat %s/* > %s' % (outdir, outpath))


# 不是真正的sample，每个分区选前count个，汇总后选count个
def sample_conv_from_sds(table_name, sample_count, start_dt_s, stop_dt_s):
    start_key = _conv_time_key(start_dt_s)
    stop_key = _conv_time_key(stop_dt_s)

    scan_iterators = sds.scan_multi_index(table_name, 'update_time_index', start_key, stop_key, False)
    task_queue = Queue()
    for it in scan_iterators:
        task_queue.put(it)

    result_queue = Queue()

    @tmtool.func_threading(daemon=True)
    def worker():
        while True:
            if task_queue.empty():
                return
            it = task_queue.get()
            count = 0
            for sds_record in it:
                post = sds_record['post']
                resp = sds_record['resp']
                line = '%s |<->| %s' % (post, resp)
                result_queue.put(line)
                count += 1
                if count >= sample_count:
                    break
                time.sleep(0.001)
            task_queue.task_done()

    ts = [worker() for _ in range(10)]
    task_queue.join()

    results = []
    while not result_queue.empty():
        results.append(result_queue.get())

    samples = [random.choice(results) for _ in range(sample_count)]
    return samples


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--tableName', help='sds table name')

    parser.add_argument('-p', '--putFile', action='store_true', default=False, help='put file convs to sds')
    parser.add_argument('--filePath', help='file path')
    parser.add_argument('--source', default=None, help='if use source for put file convs to sds')

    parser.add_argument('-d', '--download', action='store_true', default=False, help='download convs from sds')
    parser.add_argument('-c', '--count', action='store_true', default=False, help='count convs from sds')
    parser.add_argument('--sample', action='store_true', default=False, help='sample convs from sds')
    parser.add_argument('--startTime', default=None, help='start time 2017-08-01 00:00:00')
    parser.add_argument('--stopTime', default=None, help='stop time 2017-08-02 00:00:00')
    parser.add_argument('--outpath', help='out put path if download')
    parser.add_argument('--sampleCount', help='sample count')

    args = parser.parse_args()
    if args.putFile:
        convs_to_sds_from_file(args.filePath, args.tableName, args.source)
    elif args.download:
        download_conv_from_sds(args.tableName, args.outpath, args.startTime, args.stopTime)
    elif args.count:
        count_conv_fron_sds(args.tableName, args.startTime, args.stopTime)
    elif args.sample:
        samples = sample_conv_from_sds(args.tableName, int(args.sampleCount), args.startTime, args.stopTime)
        for s in samples:
            print s
