#!/usr/bin/env python
# encoding: utf-8

import os
import logging
import retrying

from thrift.TSerialization import serialize, deserialize
from thrift.protocol.TCompactProtocol import TCompactProtocol, TCompactProtocolFactory
from thrift.transport.TSocket import TSocket
from thrift.transport.TTransport import TFramedTransport

from gen_lcs_agent import LCSAgentService, Record


logger = logging.getLogger(__name__)


class LCSAgentClient(object):
    _TTransport = TFramedTransport
    _TProtocol = TCompactProtocol

    def __init__(self, cluster_name=None, org_id=None, topic_name=None, team_id=None,
                 klass=LCSAgentService, host='127.0.0.1', port=7916):
        self._klass = klass
        self._host = host
        self._port = port
        self.__reset_client__()

        self.cluster_name = cluster_name
        self.org_id = org_id
        self.topic_name = topic_name
        self.team_id = team_id

    def __reset_client__(self):
        socket = TSocket(self._host, self._port)
        socket.setTimeout(500)
        self._transport = self._TTransport(socket)
        self._transport.open()
        self.client = self._klass.Client(self._TProtocol(self._transport))

    def close(self):
        try:
            self._transport.close()
        except:
            pass

    @retrying.retry(stop_max_attempt_number=3, wait_fixed=500)
    def put(self, data, cluster_name=None, org_id=None, topic_name=None, team_id=None):
        cluster_name = cluster_name or self.cluster_name
        org_id = org_id or self.org_id
        topic_name = topic_name or self.topic_name
        team_id = team_id or self.team_id

        if isinstance(data, str):
            data = [data]
        elif isinstance(data, unicode):
            data = [data.encode('utf-8')]
        elif not isinstance(data, list):
            raise AssertionError('Not str or list')

        extend_agent_data = True

        record = Record(cluster_name, org_id, topic_name, team_id, data, extend_agent_data)

        for i in range(1, 10):
            try:
                self.client.Record(record)
            except:
                if i == 3:
                    raise
                else:
                    self.close()
                    self.__reset_client__()
            else:
                return

    def serialize_thirft(self, thrift_obj):
        data = serialize(thrift_obj, TCompactProtocolFactory())
        return data

    def deserialize_thrift(self, data, thirft_klass):
        thrift_obj = thirft_klass()
        deserialize(thrift_obj, data, TCompactProtocolFactory())
        return thrift_obj

    def serialize_put(self, data, cluster_name=None, org_id=None, topic_name=None, team_id=None):
        serialized_data = self.serialize_thirft(data)
        return self.put(serialized_data, cluster_name, org_id, topic_name, team_id)


if __name__ == '__main__':
    from douban.douban_config import LCSConfig
    client = LCSAgentClient(LCSConfig.cluster_name, LCSConfig.org_id, LCSConfig.topic_name_douban_page,
                            LCSConfig.team_id)
    # from gen_chatbot_data import ChatbotDoubanGroupPage
    # gp = ChatbotDoubanGroupPage(fetchTime=1400000, taskTag='index_page', linkinfo='okok', url='http://test.com',
    #                             rawData='你到底想说啥')
    # client.serialize_put(gp)
    content = 'This is a test'
    client.put(content)


