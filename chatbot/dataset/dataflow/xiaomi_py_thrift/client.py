import logging
import random
import inspect
from thrift.transport.TSocket import TSocket
from thrift.transport.TTransport import TFramedTransport
from thrift.protocol.TBinaryProtocol import TBinaryProtocol
from zk import MIZK


logger = logging.getLogger(__name__)


class MiThriftClient(object):
    _transport = TFramedTransport
    _protocol = TBinaryProtocol

    @staticmethod
    def __zknode_to_address__(node_name):
        host, port = node_name.strip().split(':')
        return host, int(port)

    def __init__(self, thrift_class, env, service):
        self._klass = thrift_class
        self._env = env
        self._service = service
        self._clients = dict()
        self._mizk = MIZK(self._env, self._service,
                          children_handler=self.__on_mizk_children_change__)
        self.__init_clients__()
        self.__add_thrift_method__()

    @property
    def _rand_client(self):
        addrs = self._clients.keys()
        if len(addrs) == 0:
            raise(Exception('No Valid Client Connection'))
        else:
            addr = random.choice(addrs)
            logger.debug('Random client addr is: %s', addr)
            return self._clients[addr]

    def __new_client__(self, host, port):
        transport = self._transport(TSocket(host, port))
        transport.open()
        client = self._klass.Client(self._protocol(transport))
        return client

    def __reset_clients__(self, childrens):
        logger.info('RPC Server Changed: %s' % childrens)

        old_list = self._clients.keys()
        new_list = childrens
        diff_old = set(old_list) - set(new_list)
        diff_new = set(new_list) - set(old_list)

        for k in diff_new:
            host, port = self.__zknode_to_address__(k)
            client = self.__new_client__(host, port)
            self._clients[k] = client

        for k in diff_old:
            try:
                self._clients[k].close()
            except:
                pass
            del self._clients[k]

    def __init_clients__(self):
        self.__reset_clients__(self._mizk.childrens)

    def __on_mizk_children_change__(self, childrens):
        self.__reset_clients__(childrens)

    def __exec_client_method__(self, name, *args, **kwargs):
        client = self._rand_client
        return getattr(client, name)(*args, **kwargs)

    def __create_client_executor__(self, name):
        def executor(*args, **kwargs):
            return self.__exec_client_method__(name, *args, **kwargs)
        return executor

    def __add_thrift_method__(self):
        methods = inspect.getmembers(self._klass.Iface, predicate=inspect.ismethod)
        method_names = map(lambda x: x[0], methods)
        method_names = filter(lambda x: not x.startswith('_'), method_names)
        for name in method_names:
            executor = self.__create_client_executor__(name)
            setattr(self, name, executor)

    def close(self):
        childrens = []
        self.__reset_clients__(childrens)
