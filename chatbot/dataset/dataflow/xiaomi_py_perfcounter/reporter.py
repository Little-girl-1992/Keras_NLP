#!/usr/bin/env python
# encoding: utf-8

import time
import logging
import requests

from comm import periodic_threading
from config import agent_cofing

logger = logging.getLogger(__name__)


class FalconAgentDataBuilder(object):
    @staticmethod
    def build_tags(tags):
        tags_list = ['%s=%s' % (k, v) for k, v in tags.iteritems()]
        tags_str = ','.join(tags_list)
        return tags_str

    @staticmethod
    def build_data(t, k, v, tags, ts=None):
        d = dict(
            counterType=t,
            metric=k,
            value=v,
            tags=FalconAgentDataBuilder.build_tags(tags),
            timestamp=ts or int(time.time()),
            endpoint=agent_cofing.get('endpoint'),
            step=agent_cofing.get('step')
        )
        return d


class MetricsCollector(object):
    FB = FalconAgentDataBuilder
    COUNTER = 'COUNTER'
    GAUGE = 'GAUGE'

    def __init__(self, metrics):
        self.metrics = metrics

    def build_gauge(self, name, gauge, tags):
        m1 = FalconAgentDataBuilder.build_data(self.GAUGE, name, gauge.get_value(), tags)
        return [m1]

    def build_counter(self, name, counter, tags):
        m1 = FalconAgentDataBuilder.build_data(self.COUNTER, name, counter.get_count(), tags)
        return [m1]

    def build_meter(self, name, meter, tags):
        m1 = self.FB.build_data(self.COUNTER, name, meter.get_count(), tags)
        m2 = self.FB.build_data(self.GAUGE, name + '.CPS-1-min', meter.get_one_minute_rate(), tags)
        m3 = self.FB.build_data(self.GAUGE, name + '.CPS-5-min', meter.get_five_minute_rate(), tags)
        m4 = self.FB.build_data(self.GAUGE, name + '.CPS-15-min', meter.get_fifteen_minute_rate(), tags)
        return [m1, m2, m3, m4]

    def build_hist(self, name, hist, tags):
        sn = hist.get_snapshot()
        m1 = self.FB.build_data(self.GAUGE, name + '.75-percentile', sn.get_75th_percentile(), tags)
        m2 = self.FB.build_data(self.GAUGE, name + '.95-percentile', sn.get_95th_percentile(), tags)
        m3 = self.FB.build_data(self.GAUGE, name + '.99-percentile', sn.get_99th_percentile(), tags)
        m4 = self.FB.build_data(self.GAUGE, name + '.999-percentile', sn.get_999th_percentile(), tags)
        return [m1, m2, m3, m4]

    def build_timer(self, name, timer, tags):
        ms1 = self.build_meter(name, timer.meter, tags)
        ms2 = self.build_hist(name, timer.hist, tags)
        return ms1 + ms2

    def build_falcon_data(self):
        ms = []
        for k, v in self.metrics.get_gauges().iteritems():
            ms += self.build_gauge(k, v, self.metrics.get_tags(k))
        for k, v in self.metrics.get_counters().iteritems():
            ms += self.build_counter(k, v, self.metrics.get_tags(k))
        for k, v in self.metrics.get_meters().iteritems():
            ms += self.build_meter(k, v, self.metrics.get_tags(k))
        for k, v in self.metrics.get_hists().iteritems():
            ms += self.build_hist(k, v, self.metrics.get_tags(k))
        for k, v in self.metrics.get_timers().iteritems():
            ms += self.build_timer(k, v, self.metrics.get_tags(k))
        return ms


class PerfReporter(object):
    def __init__(self, registry=None, reporting_interval=agent_cofing['step']):
        self.metrics = registry
        self.reporting_interval = reporting_interval
        self.periodic_report_t = None

    def push_to_agent(self, data):
        logger.debug('Push to falcon agent ...')
        for _ in range(3):
            try:
                res = requests.request('POST', agent_cofing.get('agent_uri'), json=data, timeout=1)
            except Exception as e:
                logger.exception(e)
                logger.warn('Push to falcon agent exception, retrying...')
                continue
            else:
                if not res.ok:
                    logger.warn('Push to falcon agent is not ok, retrying...')
                    continue
                else:
                    logger.debug('Push to falcon agent succeed')
                    return
        logger.warn('Push to falcon agent failure 3 times, stop retry')

    def collect(self):
        mc = MetricsCollector(self.metrics)
        falcon_data = mc.build_falcon_data()
        return falcon_data

    def report_now(self, registry=None, timestamp=None):
        data = self.collect()
        self.push_to_agent(data)

    def start(self):
        self.periodic_report_t = periodic_threading(self.reporting_interval)(self.report_now)()

    def stop(self):
        if self.periodic_report_t is not None:
            self.periodic_report_t.stop()
