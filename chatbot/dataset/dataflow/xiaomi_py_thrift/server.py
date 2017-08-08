#!/usr/bin/env python
# encoding: utf-8


import os
import atexit
import signal
import logging

from zk import MIZK

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

logger = logging.getLogger(__name__)


class MiThriftServerOption(object):

    def __init__(self, env=None, service=None, host='localhost', port=9090):
        self.itransf = TTransport.TFramedTransportFactory()
        self.otransf = TTransport.TFramedTransportFactory()
        self.iprotof = TBinaryProtocol.TBinaryProtocolFactory()
        self.oprotof = TBinaryProtocol.TBinaryProtocolFactory()
        self.host = host
        self.port = port
        self.env = env or 'STAGING'
        self.service = service or 'com.miui.testPy.thrift.TestService'


class MiThriftServer(object):

    def __init__(self, handler, option=None):
        self.handler = handler
        self.option = option or MiThriftServerOption()
        self.server = None

    def __remove_zk_then_exit__(self, signum=None, framed=None):
        logger.info('Receive signal: %s, will remove zk service then exit', signum)
        try:
            self.mizk.remove_service()
            self.mizk.close()
        except:
            pass
        os._exit(1)

    def __register_signal_handler__(self):
        signal.signal(signal.SIGINT, self.__remove_zk_then_exit__)
        signal.signal(signal.SIGTERM, self.__remove_zk_then_exit__)
        signal.signal(signal.SIGQUIT, self.__remove_zk_then_exit__)
        signal.signal(signal.SIGABRT, self.__remove_zk_then_exit__)
        atexit.register(self.__remove_zk_then_exit__)

    def __init_zk__(self):
        self.mizk = MIZK(self.option.env, self.option.service, self.option.port)
        self.mizk.register_service()
        self.__register_signal_handler__()

    def run(self):
        transport = TSocket.TServerSocket(host=self.option.host, port=self.option.port)
        self.__init_zk__()
        self.server = TServer.TThreadedServer(self.handler, transport,
                                              self.option.itransf, self.option.otransf,
                                              self.option.iprotof, self.option.oprotof)
        logger.info('Listening on %s:%s' % (self.option.host, self.option.port))
        self.server.serve()
