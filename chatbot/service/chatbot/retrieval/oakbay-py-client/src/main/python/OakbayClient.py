# !/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os
import sys

sys.path.append("../python")
reload(sys)
sys.setdefaultencoding("utf-8")

import logging
logger = logging.getLogger(__file__)

import itertools

from kazoo.client import KazooClient

from oakbayThrift.OakbayClient import *

from thrift import Thrift
from thrift.transport import TSocket, TTransport
from thrift.protocol import TBinaryProtocol

zk_production_lg = "lg-com-master01.bj:11000,lg-com-master02.bj:11000,lg-hadoop-srv-ct01.bj:11000," \
                   "lg-hadoop-srv-ct02.bj:11000,lg-hadoop-srv-ct03.bj:11000/oakbay/v2"
zk_production_c3 = "c3-hadoop-srv-ct06.bj:11000,c3-hadoop-srv-ct07.bj:11000,c3-hadoop-srv-ct08.bj:11000," \
                   "c3-hadoop-srv-ct09.bj:11000,c3-hadoop-srv-ct10.bj:11000/oakbay/v2"
zk_production_c4 = "c4-hadoop-srv-ct06.bj:11000,c4-hadoop-srv-ct07.bj:11000,c4-hadoop-srv-ct08.bj:11000," \
                   "c4-hadoop-srv-ct09.bj:11000,c4-hadoop-srv-ct10.bj:11000/oakbay/v2"
zk_staging = "zk1.staging.srv:2181,zk2.staging.srv:2181,zk3.staging.srv:2181,zk4.staging.srv:2181,zk5.staging.srv:2181/oakbay_v2/oakbay"


class OakbayClient:
    kazoo = None

    def __init__(self, env, timeout):
        """
        :param env: environment name
        :param timeout:
        :return:
        """
        self.clients = {}
        self.clientIter = None
        self.timeout = int(timeout)
        self.children_listeners = {}
        self.data_listeners = {}
        if env.lower() == 'staging':
            zk_cluster_url = zk_staging
        elif env.lower() == 'lg':
            zk_cluster_url = zk_production_lg
        elif env.lower() == 'c3':
            zk_cluster_url = zk_production_c3
        elif env.lower() == 'c4':
            zk_cluster_url = zk_production_c4
        else:
            raise Exception("invalid env name")

        self.init(zk_cluster_url)

    def init(self, url):
        """
        :param is_search: is search cluster
        :param url:
        :return:
        """
        pos = url.find("/")
        servers_ports = url[:pos]
        self.kazoo = KazooClient(hosts=servers_ports)
        self.kazoo.start()

        base_path = url[pos:]
        master_node_path = os.path.join(base_path, 'master', 'master_node')

        @self.kazoo.ChildrenWatch(master_node_path)
        def update(children):
            logger.debug("Master nodes are %s" % children)
            new_clients = {};
            for child in children:
                if child in self.clients:
                    new_clients[child] = self.clients[child]
                    logger.debug('Reuse client from ' + child)
                else:
                    new_clients[child] = self.parse_client(os.path.join(master_node_path, child))
                    logger.debug('New client created from ' + child)

            tmp_clients = self.clients
            self.clients = new_clients
            self.clientIter = itertools.cycle(self.clients.values())

            for k, v in tmp_clients.iteritems():
                if k not in self.clients:
                    v.close()

    def close(self):
        self.kazoo.stop()
        self.kazoo.close()

    def get_client(self):
        return self.clientIter.next()

    def parse_client(self, path):
        data = self.kazoo.get(path).__getitem__(0)
        json_instance = json.loads(data)
        return self.build(json_instance)

    def build(self, json_instance):
        json_service_endpoint = json_instance["serviceEndpoint"]
        if json_service_endpoint is not None:
            host = json_service_endpoint["host"]
            port = int(json_service_endpoint["port"])
            if host is not None and port is not None:
                return FinagleClient(host, port, self.timeout)
        raise Exception("read end point data error")


class FinagleClient:
    def __init__(self, host, port, timeout):
        self.srv = "%s:%s" % (host, port)
        socket = TSocket.TSocket(host, port)
        socket.setTimeout(timeout)
        self.transport = TTransport.TFramedTransport(socket)
        self.transport.open()
        self.client = OakbayClientService.Client(TBinaryProtocol.TBinaryProtocol(self.transport))
        pass

    def close(self):
        self.transport.close()

    def get(self):
        return self.client

    def __str__(self):
        return self.srv


def main():
    oakbay_client = OakbayClient("staging", 3000)

    finagle_client = oakbay_client.get_client()
    try:
        client = finagle_client.get()

        domain = "misearch"
        cluster = "appstore-search-v2-preview"
        bql = "select * from linden limit 0, 1"
        result = client.handleBqlRequest(domain, cluster, bql)
        logger.debug(result)

        # close
        for k, v in oakbay_client.clients.iteritems():
            v.close()
        oakbay_client.close()

    except Thrift.TException, ex:
        logger.debug("%s" % ex)


if __name__ == '__main__':
    main()
