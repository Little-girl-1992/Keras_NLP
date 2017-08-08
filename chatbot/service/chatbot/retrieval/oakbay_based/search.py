#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import jieba
import logging

from OakbayClient import OakbayClient

reload(sys)
sys.setdefaultencoding('utf8')

logger = logging.getLogger(__file__)

ENV = 'c3'
DOMAIN = 'chatbot'
CLUSTER = 'chatbot_0.1'
LIMIT = 50

SEP = ' |<->| '


def test():
  client = OakbayClient(ENV, 4000).get_client().get()
  bql = 'select * from LINDEN limit 0, 1'
  print(client.handleBqlRequest(DOMAIN, CLUSTER, bql))


class Tokenizer(object):
  @staticmethod
  def cut(s):
    s = ''.join(s.split())
    words = list(jieba.cut(s))
    return words


class SearchClient(object):
  def __init__(self, env=ENV, use_cut=True):
    self._oakbay_client = OakbayClient(env, 3000)
    self.use_cut = use_cut
    self.cut = Tokenizer.cut

  def rand_client(self):
    return self._oakbay_client.get_client().get()

  def close(self):
    for client in self._oakbay_client.clients.itervalues():
      client.close()
    self._oakbay_client.close()

  def make_bql(self, text, limit, only_post):
    if only_post:
      bql = 'select * from LINDEN by query is "post:(%s)" limit 0, %d source' % \
            (text, limit)
    else:
      bql = 'select * from LINDEN by query is "post:(%s) OR resp:(%s)" limit 0, %d source' % \
            (text, text, limit)
    logger.debug('BQL: %s' % bql)
    return bql

  def request_search(self, text, limit, domain, cluster, only_post):
    bql = self.make_bql(text, limit, only_post)
    result = self.rand_client().handleBqlRequest(domain, cluster, bql)
    return result

  def search(self, query, limit=LIMIT, domain=DOMAIN, cluster=CLUSTER, only_post=True):
    if self.use_cut:
      query_words = self.cut(query)
      processed_query = ' '.join(query_words).encode('utf8')
    else:
      processed_query = query
    request_result = self.request_search(processed_query, limit, domain, cluster, only_post)

    if not request_result.success:
      raise Exception(request_result.error)

    top_hits = []
    linden_result = request_result.lindenResult
    logger.debug('Total hits: %d, TOP 100: ' % (linden_result.totalHits))
    for hit in linden_result.hits:
      source = json.loads(hit.source)
      top_hits.append(dict(score=hit.score, source=dict(post=source['post'], resp=source['resp'])))
      logger.debug('%s%s%s%s%s' % (hit.score, SEP, source['post'], SEP, source['resp']))

    result = dict(
      origin_query=query,
      processed_query=processed_query,
      total_hits=linden_result.totalHits,
      limit=limit,
      top_hits=top_hits
    )
    return result

  def search_all(self, domain, cluster, total):
    batch = 10000
    start = 0
    results = []
    while True:
      if start < total:
        bql = 'select * from linden limit %s, %s source' % (start, batch)
        result = self.rand_client().handleBqlRequest(domain, cluster, bql)
        linden_result = result.lindenResult
        for hit in linden_result.hits:
          logger.debug(hit.source)
          results.append(hit.source)
        start = start + batch
      else:
        break
    return results


if __name__ == '__main__':
  logging.basicConfig(level='DEBUG')

  # env = sys.argv[1]
  # domain = sys.argv[2]
  # cluster = sys.argv[3]
  # query = sys.argv[4]
  env = 'c3'
  domain = 'chatbot'
  cluster = 'chatbot_douban_0.1'
  query = '爱撒娇的女人有好命'
  client = SearchClient(env, False)
  only_post = True
  # client.search_all('chatbot', 'chatbot-hot-query-back', 48788)
  hits = client.search(query, limit=30, domain=domain, cluster=cluster, only_post=only_post)
  print(hits)
  client.close()
