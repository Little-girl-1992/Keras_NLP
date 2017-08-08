#!/usr/bin/env python
# encoding: utf-8

import os
import logging
from kazoo.client import KazooClient
from kazoo.exceptions import NoNodeError

logger = logging.getLogger(__name__)


ZK_HOSTS = {
    'mine': '127.0.0.1:2181',
    'STAGING': 'zk1.staging.srv:2181,zk2.staging.srv:2181,zk3.staging.srv:2181,zk4.staging.srv:2181,zk5.staging.srv:2181',
    'C3': 'c3-hadoop-srv-ct06.bj:11000,c3-hadoop-srv-ct07.bj:11000,c3-hadoop-srv-ct08.bj:11000,c3-hadoop-srv-ct09.bj:11000,c3-hadoop-srv-ct10.bj:11000',
    'production-lg': 'lg-com-master01.bj:11000,lg-com-master02.bj:11000,lg-hadoop-srv-ct01.bj:11000,lg-hadoop-srv-ct02.bj:11000,lg-hadoop-srv-ct03.bj:11000'
}


def get_ip_address(ifname):
    import socket
    import fcntl
    import struct

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,
        struct.pack('256s', ifname[:15])
    )[20:24])


def get_local_ipv4():
    return get_ip_address('eth0')


class MIZK(object):

    def __init__(self, env, service, port=None, children_handler=None):
        self.env = env
        self.service = service
        self.port = str(port or 8000)
        self.client = KazooClient(hosts=ZK_HOSTS.get(self.env, ZK_HOSTS['mine']))
        self.client.add_listener(MIZK.__state_listener__)
        self.client.start()
        if children_handler is not None:
            self.watch(children_handler)

    @staticmethod
    def __state_listener__(state):
        logger.info('ZooKeeper State: %s' % state)

    @staticmethod
    def __dict_to_ini__(d):
        cs = ['%s=%s' % (k, v) for k, v in d.iteritems()]
        return '\n'.join(cs)

    @property
    def _service_pool_path(self):
        pool_path = os.path.join('/services', self.service, 'Pool')
        return pool_path

    @property
    def _node_path(self):
        ip = get_local_ipv4()
        if ip is None:
            raise(Exception('Can not get IP'))
        node_name = ip + ':' + self.port
        return os.path.join(self._service_pool_path, node_name)

    @property
    def _node_data(self):
        conf = {
            'version': 1,
            'server.service.level': 10,
            'implementation': self.service,
            'thrift.runner.zookeeper.config': '/services/' + self.service + '/Configuration/Default',
            'host': get_local_ipv4(),
            'port': self.port,
            'weight': 10,
        }
        return MIZK.__dict_to_ini__(conf)

    def watch(self, handler):
        @self.client.ChildrenWatch(self._service_pool_path)
        def child_watch(children):
            handler(children)

    @property
    def childrens(self):
        childrens = self.client.get_children(self._service_pool_path)
        return childrens

    def register_service(self):
        try:
            self.remove_service()
        except NoNodeError:
            pass
        self.client.create(self._node_path, bytes(self._node_data), ephemeral=True, makepath=True)

    def remove_service(self):
        self.client.delete(self._node_path)

    def close(self):
        self.client.stop()
        self.client.close()
