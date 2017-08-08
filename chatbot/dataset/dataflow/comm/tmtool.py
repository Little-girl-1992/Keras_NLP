#!/usr/bin/env python
# encoding: utf-8

import time
import hashlib
import datetime
import functools
import threading
import Queue
import multiprocessing


date_fmt = '%Y-%m-%d'
time_fmt = '%H:%M:%S'
datetime_fmt = '%Y-%m-%d %H:%M:%S'


def datetime_2_ts(dt):
    total_seconds = (dt - datetime.datetime(1970, 1, 1)).total_seconds()
    return int(total_seconds) * 1000


def datetime_str_2_datetime(s):
    return datetime.datetime.strptime(s, datetime_fmt)


def datetime_str_2_ts(s):
    dt = datetime_str_2_datetime(s)
    ts = datetime_2_ts(dt)
    return ts


def now_ts():
    return int(time.time() * 1000)


def datetime_ds(dt):
    days = (dt - datetime.datetime.fromtimestamp(0)).days
    return days


def date_ds(dt):
    days = (dt - datetime.date.fromtimestamp(0)).days
    return days


def today_ds():
    days = date_ds(datetime.date.today())
    return days


def ds_fmt(ds):
    d = datetime.date.fromtimestamp(ds * 3600 * 24)
    s = d.strftime(date_fmt)
    return s


def md5(s):
    m = hashlib.md5()
    m.update(s)
    return m.hexdigest()


def now_fmt():
    now = datetime.datetime.now()
    return now.strftime(datetime_fmt)


def periodic(interval, timers=None):
    def args_func(func):
        @functools.wraps(func)
        def action_func(*args):
            t = threading.Timer(interval, action_func, args)
            t.start()

            if isinstance(timers, set):
                timers.add(t)
                stopped_timers = filter(lambda x: not x.isAlive(), timers)
                for st in stopped_timers:
                    timers.remove(st)

            return func(*args)
        return action_func
    return args_func


class StoppableThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


def func_threading(daemon=True, name_prefix='threading'):
    def args_func(func):
        @functools.wraps(func)
        def action_func(*args, **kwargs):
            t = StoppableThread(target=func, args=args, kwargs=kwargs)
            t.setName('%s_%s' % (name_prefix, func.func_name))
            t.setDaemon(daemon)
            t.start()
            return t
        return action_func
    return args_func


def func_processing(daemon=True, name_prefix='processing'):
    def args_func(func):
        @functools.wraps(func)
        def action_func(*args, **kwargs):
            p = multiprocessing.Process(target=func, args=args, kwargs=kwargs)
            p.name = '%s_%s' % (name_prefix, func.func_name)
            p.daemon = daemon
            p.start()
            return p
        return action_func
    return args_func


def periodic_threading(interval, daemon=True, name_prefix='periodic_threading'):
    def args_func(func):

        @func_threading(daemon, name_prefix)
        def _loop(*args, **kwargs):
            t = threading.currentThread()
            while not t.stopped():
                func(*args, **kwargs)
                time.sleep(interval)

        @functools.wraps(func)
        def action_func(*args, **kwargs):
            t = _loop(*args, **kwargs)
            return t
        return action_func

    return args_func


def parallel(tasks, worker, limit=10, use_process=False):
    if use_process:
        task_queue = multiprocessing.Queue()
        result_queue = multiprocessing.Queue()
    else:
        task_queue = Queue.Queue()
        result_queue = Queue.Queue()

    for t in tasks:
        task_queue.put(t)

    if use_process:
        parallel_worker = func_processing(daemon=True)(worker)
    else:
        parallel_worker = func_threading(daemon=True)(worker)

    ts = [parallel_worker(task_queue, result_queue) for _ in range(limit)]
    for t in ts:
        t.join()

    results = []
    while not result_queue.empty():
        results.append(result_queue.get())

    return results
