#!/usr/bin/env python
# encoding: utf-8

from retrying import retry
from xiaomi_py_thrift import MiThriftClient
from gen_crawler import TaskResponse, TaskRequest, CrawlerService


class MiCrawlerClient(object):
    service_name = 'com.xiaomi.micrawler.thrift.CrawlerService'

    def __init__(self, env=None, business_name=None):
        self._env = env
        self._service_name = MiCrawlerClient.service_name
        self._business_name = business_name
        self.client = MiThriftClient(CrawlerService, self._env, self._service_name)

    @retry(stop_max_attempt_number=3)
    def submit_tasks(self, urls, task_tag):
        request = TaskRequest(
            urls=set(urls),
            businessName=self._business_name,
            taskTag=task_tag
        )
        res = self.client.submitTask(request)
        if not res.success:
            raise Exception(res.error)
        return res
