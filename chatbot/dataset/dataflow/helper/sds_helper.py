#!/usr/bin/env python
# encoding: utf-8

import os
import time
import itertools
import retrying

from sds.auth.ttypes import Credential
from sds.auth.ttypes import UserType
from sds.client.clientfactory import ClientFactory
from sds.client.datumutil import datum
from sds.client.datumutil import values
from sds.common.constants import ADMIN_SERVICE_PATH
from sds.common.constants import DEFAULT_ADMIN_CLIENT_TIMEOUT
from sds.common.constants import DEFAULT_CLIENT_TIMEOUT
from sds.common.constants import TABLE_SERVICE_PATH
from sds.table.ttypes import DataType
from sds.table.ttypes import Datum
from sds.table.ttypes import GetRequest
from sds.table.ttypes import IncrementRequest
from sds.table.ttypes import PutRequest
from sds.table.ttypes import ScanRequest
from sds.table.ttypes import BatchOp, BatchRequestItem, BatchRequest, Request


""" overwrite table scanner -- begging"""
from time import sleep
from sds.client.datumutil import values


def retry_exec(func, *args, **kwargs):
    func = retrying.retry(stop_max_attempt_number=3, wait_fixed=500)(func)
    return func(*args, **kwargs)


def datum_scan_iter(table_client, scan):
    terminated = False
    retry = 0
    while not terminated:
        if retry >= 1:
            # throttling the request
            sleep(0.5 * (1 << (retry - 1)))

        # 加入重试
        result = retry_exec(table_client.scan, scan)
        terminated = result.nextStartKey is None
        records = result.records
        scan.startKey = result.nextStartKey
        if not terminated and len(records) < scan.limit and result.throttled:
            retry += 1
        else:
            retry = 0

        for record in records:
            yield record


def scan_iter(table_client, scan):
  for record in datum_scan_iter(table_client, scan):
    yield values(record)


""" overwrite table scanner -end"""


class SDSHelper(object):
    def __init__(self, app_key, app_secret, endpoint='http://cnbj1-sds.api.xiaomi.net'):
        self._app_key = app_key
        self._app_secret = app_secret
        self._endpoint = endpoint
        self._credential = Credential(UserType.APP_SECRET, self._app_key, self._app_secret)
        self._client_factory = ClientFactory(self._credential, True)
        self.table_client = self._client_factory.new_table_client(self._endpoint + TABLE_SERVICE_PATH,
                                                                  DEFAULT_CLIENT_TIMEOUT)
        self._admin_client = self._client_factory.new_admin_client(self._endpoint + ADMIN_SERVICE_PATH,
                                                                   DEFAULT_ADMIN_CLIENT_TIMEOUT)

    def _datum(self, v):
        t = type(v)
        if t == Datum:
            dv = v
        elif t == int:
            dv = datum(v, DataType.INT64)
        elif t == float:
            dv = datum(v, DataType.DOUBLE)
        elif t == unicode:
            v = v.encode('utf-8')
            dv = datum(v)
        elif t == buffer:
            dv = datum(v, DataType.BINARY)
        else:
            dv = datum(v)
        return dv

    def _datum_dict(self, d):
        if d is not None:
            d = {k: self._datum(v) for k, v in d.iteritems()}
        return d

    @retrying.retry(stop_max_attempt_number=3, wait_fixed=500)
    def get(self, table_name, keys, attributes=None):
        keys = self._datum_dict(keys)
        gr = GetRequest(
            tableName=table_name,
            keys=keys,
            attributes=attributes
        )
        res = self.table_client.get(gr).item
        if res is not None:
            res = values(res)
        return res

    @retrying.retry(stop_max_attempt_number=3, wait_fixed=500)
    def put(self, table_name, record, condition=None):
        record = self._datum_dict(record)
        pr = PutRequest(
            tableName=table_name,
            record=record,
            condition=condition
        )
        res = self.table_client.put(pr)

        return res

    @retrying.retry(stop_max_attempt_number=3, wait_fixed=500)
    def batch_put(self, table_name, records, condition=None):
        items = []
        for r in records:
            r = self._datum_dict(r)
            pr = PutRequest(
                tableName=table_name,
                record=r,
                condition=condition
            )
            item = BatchRequestItem(BatchOp.PUT, Request(putRequest=pr))
            items.append(item)
        br = BatchRequest(items)
        res = self.table_client.batch(br)
        return res

    def scan(self, table_name, start_key=None, stop_key=None, **extra_args):
        start_key = self._datum_dict(start_key)
        stop_key = self._datum_dict(stop_key)
        args = dict(
            tableName=table_name,
            startKey=start_key,
            stopKey=stop_key,
            limit=30
        )
        args.update(extra_args)
        sr = ScanRequest(**args)
        return scan_iter(self.table_client, sr)

    def scan_multi(self, table_name, start_key=None, stop_key=None, one_iterator=True,
                   use_table_splits=False, **extra_args):
        start_key = self._datum_dict(start_key)
        stop_key = self._datum_dict(stop_key)
        table_splits = self._admin_client.getTableSplits(table_name, start_key, stop_key)

        if use_table_splits:
            return table_splits

        extra_args.update(inGlobalOrder=False)
        splits_scans = []
        for table in table_splits:
            scan_iterator = self.scan(table_name, table.startKey, table.stopKey, **extra_args)
            splits_scans.append(scan_iterator)
        if one_iterator:
            return itertools.chain(*splits_scans)
        else:
            return splits_scans

    def scan_multi_index(self, table_name, index_name, start_key=None, stop_key=None, one_iterator=True,
                         use_table_splits=False, **extra_args):
        start_key = self._datum_dict(start_key)
        stop_key = self._datum_dict(stop_key)
        table_splits = self._admin_client.getIndexTableSplits(table_name, index_name, start_key, stop_key)

        if use_table_splits:
            return table_splits

        extra_args.update(indexName=index_name)
        extra_args.update(inGlobalOrder=False)
        splits_scans = []
        for table in table_splits:
            scan_iterator = self.scan(table_name, table.startKey, table.stopKey, **extra_args)
            splits_scans.append(scan_iterator)
        if one_iterator:
            return itertools.chain(*splits_scans)
        else:
            return splits_scans

    @retrying.retry(stop_max_attempt_number=3, wait_fixed=500)
    def increment(self, table_name, keys, amounts):
        keys = self._datum_dict(keys)
        amounts = self._datum_dict(amounts)
        ir = IncrementRequest(
            tableName=table_name,
            keys=keys,
            amounts=amounts
        )
        res = self.table_client.increment(ir)
        return res


if __name__ == '__main__':
    from douban.douban_config import SDSConfig
    sds = SDSHelper(SDSConfig.chatbot_app_key, SDSConfig.chatbot_app_secret)
    table_name = SDSConfig.chatbot_meta_table_name

    print(sds.get(table_name, keys={'topicType': 'start'}))
    print(sds.put(table_name, {'topicType': 'test', 'topicId': 12345, 'updateTime': 1234567890}))
    print(sds.increment(table_name, {'topicType': 'test'}, {'topicId': 10}))
    for r in sds.scan(table_name):
        print(r)
