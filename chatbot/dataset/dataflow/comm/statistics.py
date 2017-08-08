#!/usr/bin/env python
# encoding: utf-8


import copy
import logging

import tmtool
from collections import defaultdict
from helper.sds_helper import SDSHelper

logger = logging.getLogger(__name__)


class Statistics(object):
    def __init__(self, update_interlval=60, statistic_table_name=None, app_key=None, app_secret=None):
        self._table_name = statistic_table_name
        self._app_key = app_key
        self._app_secret = app_secret

        self._sds = SDSHelper(self._app_key, self._app_secret)
        self._cache_counts = defaultdict(int)
        self._cache_existed_rows = set()

        self._timers = set()
        self._update_interval = update_interlval

        self.run_t = None

    def joint_key(self, time, name):
        return '%s_%s' % (time, name)

    def split_key(self, key):
        parts = key.split('_')
        return int(parts[0]), '_'.join(parts[1:])

    def check_table_row(self, ds, name):
        row = self._sds.get(self._table_name, keys={'time': ds, 'name': name})
        return row is not None

    def ensure_table_row(self, ds, name):
        if not self.check_table_row(ds, name):
            fmt_time = tmtool.ds_fmt(ds)
            self._sds.put(self._table_name,
                          record={'time': ds, 'name': name, 'count': 0, 'fmtTime': fmt_time}
                          )

    def incr_key_count(self, time_name, count):
        time, name = self.split_key(time_name)
        if time_name not in self._cache_existed_rows:
            self.ensure_table_row(time, name)
            self._cache_existed_rows.add(time_name)

        self._sds.increment(self._table_name,
                            keys={'time': time, 'name': name},
                            amounts={'count': count}
                            )

    def _incr_all(self):
        logger.info('Increment all statistics count')
        cache_counts = copy.copy(self._cache_counts)
        self._cache_counts.clear()

        for time_name, count in cache_counts.iteritems():
            if count != 0:
                self.incr_key_count(time_name, count)

    def record(self, name, count):
        ds = tmtool.today_ds()
        key = self.joint_key(ds, name)
        self._cache_counts[key] += count

    def flush(self):
        logger.info('Flush all statistic counts in cache')
        self._incr_all()

    # Should call only once before call stop()
    def start(self):
        logger.info('Start periodic increment scheduler')
        periodic_incr_all = tmtool.periodic_threading(self._update_interval)(self._incr_all)
        self.run_t = periodic_incr_all()

    def stop(self):
        logger.info('Stop periodic increment scheduler')
        if self.run_t is not None:
            self.run_t.stop()

    def clear(self):
        logger.info('Clear all statistic counts in cache')
        self._cache_counts.clear()
