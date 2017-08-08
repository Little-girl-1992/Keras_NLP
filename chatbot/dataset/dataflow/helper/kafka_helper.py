#!/usr/bin/env python
# encoding: utf-8

import time
from threading import Thread
from kafka import KafkaConsumer


class Consumer(object):

    def __init__(self, topics, broker_servers, group_id, *args, **kwargs):
        self.consumer = KafkaConsumer(topics, bootstrap_servers=broker_servers, group_id=group_id,
                                      enable_auto_commit=False, auto_commit_interval_ms=1000,
                                      auto_offset_reset='earliest', *args, **kwargs)
        self._commit_interval_ms = 1000
        # self._loop_commit()

    # DO NOT USE !
    # KafkaConsumer is not thread safe
    def _loop_commit(self):
        self._loop_commit_thread = Thread(target=self._periodic_commit)
        self._loop_commit_thread.setName('kafka_conuser_auto_commit_thread')
        self._loop_commit_thread.setDaemon(True)
        self._loop_commit_thread.start()

    def _periodic_commit(self):
        while True:
            self.consumer.commit()
            time.sleep(self._commit_interval_ms / 1000.0)

    def get(self):
        return self.consumer

