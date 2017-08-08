#!/usr/bin/env python
# encoding: utf-8

import os
import pyformance
import multiprocessing
from collections import defaultdict

from reporter import PerfReporter
from comm import periodic_threading, func_threading

try:
    from synchronize import make_synchronized
except ImportError:
    def make_synchronized(func):
        import threading
        func.__lock__ = threading.Lock()

        def synced_func(*args, **kws):
            with func.__lock__:
                return func(*args, **kws)

        return synced_func


class Singleton(object):
    instance = None

    @make_synchronized
    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = object.__new__(cls, *args, **kwargs)
        return cls.instance


class PerfCounter(Singleton):
    def __init__(self):
        self._tags = dict()
        self._metrics = pyformance.global_registry()
        self.count_calls = pyformance.count_calls
        self.meter_calls = pyformance.meter_calls
        self.hist_calls = pyformance.hist_calls
        self.timer_calls = pyformance.time_calls

    def run(self):
        self.reporter = PerfReporter(self)
        self.reporter.start()

    def get_gauge(self, k):
        return self._metrics.gauge(k)

    def get_gauges(self):
        return self._metrics._gauges

    def set_gauge(self, k, v):
        self._metrics.gauge(k).set_value(v)

    def get_counter(self, k):
        return self._metrics.counter(k)

    def get_counters(self):
        return self._metrics._counters

    def inc_counter(self, k, v=1):
        self._metrics.counter(k).inc(v)

    def get_meter(self, k):
        return self._metrics.meter(k)

    def get_meters(self):
        return self._metrics._meters

    def mark_meter(self, k, v=1):
        self._metrics.meter(k).mark(v)

    def get_timer(self, k):
        return self._metrics.timer(k)

    def get_timers(self):
        return self._metrics._timers

    def add_timer(self, k, v):
        self.get_timer(k).meter.mark(v)
        self.get_timer(k).hist.add(v)

    def time_timer(self, k):
        # 返回的是 context，可以使用 with statement
        return self._metrics.timer(k).time()

    def get_hist(self, k):
        return self._metrics.histogram(k)

    def get_hists(self):
        return self._metrics._histograms

    def add_hist(self, k, v):
        self._metrics.histogram(k).add(v)

    def add_tags(self, k, tags):
        if k not in self._tags:
            self._tags[k] = {}
        for tk, tv in tags.iteritems():
            self._tags[k][tk] = tv

    def get_tags(self, k):
        if k not in self._tags:
            self._tags[k] = {}
        return self._tags[k]

    def count(self, k, v=1):
        self.mark_meter(k, v)

    def duration(self, k, v):
        return self.add_timer(k, v)

    def dump_metrics(self):
        return self._metrics.dump_metrics()

    def reporter_collect(self):
        return self.reporter.collect()

    def clear(self):
        self._metrics.clear()

    def flush(self):
        self.reporter.report_now()


class ClusterPerfCounter(object):
    def __init__(self, queue, worker_name_flag='NOT_MASTER'):
        self.queue = queue
        self.worker_name_flag = worker_name_flag

    # 在进程之内执行
    def run(self):
        self.check_master()
        self.init_metrics()

        if self.is_master:
            self._recv_t = None
            self._perfcounter = PerfCounter()
            self.start_recv()

        self.send_interval = 1
        self.perioic_send_t = None
        self.start_send()

    def check_master(self):
        pname = multiprocessing.current_process().name
        if self.worker_name_flag in pname:
            self.is_master = False
        else:
            self.is_master = True

    def init_metrics(self):
        self.tags = defaultdict(dict)
        self.gauges = dict()
        self.counters = defaultdict(int)
        self.meters = defaultdict(int)
        self.hists = defaultdict(list)
        self.timers = defaultdict(list)

    def set_gauge(self, k, v):
        self.gauges[k] = v

    def inc_counter(self, k, v=1):
        self.counters[k] += v

    def mark_meter(self, k, v=1):
        self.meters[k] += v

    def add_hist(self, k, v):
        self.hists[k].append(v)

    def add_timer(self, k, v):
        self.timers[k].append(v)

    def count(self, k, v=1):
        self.mark_meter(k, v)

    def duration(self, k, v):
        self.add_timer(k, v)

    def add_tags(self, k, tags):
        for tn, tv in tags:
            self.tags[k][tn] = tv

    def send_to_master(self):
        if self.counters or self.meters or self.hists or self.timers or self.tags:
            data = dict(
                pid=os.getpid(),
                type='PUSH_METRICS',
                value=dict(
                    gauges=self.gauges,
                    counters=self.counters,
                    meters=self.meters,
                    hists=self.hists,
                    timers=self.timers,
                    tags=self.tags
                )
            )
            self.queue.put(data)
            self.init_metrics()

    def recv_message(self):
        while True:
            message = self.queue.get()
            if message['type'] != 'PUSH_METRICS':
                continue
            metrics = message['value']
            for k, v in metrics['gauges'].iteritems():
                self._perfcounter.set_gauge(k, v)
            for k, v in metrics['counters'].iteritems():
                self._perfcounter.inc_counter(k, v)
            for k, v in metrics['meters'].iteritems():
                self._perfcounter.mark_meter(k, v)
            for k, v in metrics['hists'].iteritems():
                for n in v:
                    self._perfcounter.add_hist(k, n)
            for k, v in metrics['timers'].iteritems():
                for n in v:
                    self._perfcounter.add_timer(k, n)
            for k, v in metrics['tags'].iteritems():
                self._perfcounter.add_tags(k, v)

    def start_send(self):
        self.perioic_send_t = periodic_threading(self.send_interval)(self.send_to_master)()

    def stop_send(self):
        if self.perioic_send_t is not None:
            self.perioic_send_t.stop_send()

    def start_recv(self):
        self._recv_t = func_threading(daemon=True)(self.recv_message)()

    def flush(self):
        self.send_to_master()

    def clear(self):
        self.init_metrics()
