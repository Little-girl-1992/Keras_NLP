#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import logging

from OakbayClient import OakbayClient


SEP = ' |<->| '
ENV = 'staging'
DOMAIN = 'chatbot'
CLUSTER = 'chatbot-weibo'
LIMIT = 100

logger = logging.getLogger(__file__)


class ConvClient(object):
    # https://lucene.apache.org/core/2_9_4/queryparsersyntax.html
    SPECIAL_CHARS = set('+ - & | ! ( ) { } [ ] ^ " ~ * ? : \ /'.split())

    def __init__(self, env=ENV, domain=DOMAIN):
        self.env = env
        self.domain = domain
        self._oakbay_client = OakbayClient(self.env, 3000)

    def _rand_client(self):
        return self._oakbay_client.get_client().get()

    def close(self):
        for client in self._oakbay_client.clients.itervalues():
            client.close()
        self._oakbay_client.close()

    def escape(self, s):
        ns = ''
        for c in s:
            if c in self.SPECIAL_CHARS:
                c = '\\' + c
            ns += c
        return ns

    def _make_search_bql(self, text, limit, only_post):
        text = self.escape(text)
        if only_post:
            bql = 'select * from LINDEN by query is "post:(%s)" limit 0, %d source' % \
                (text, limit)
        else:
            bql = 'select * from LINDEN by query is "post:(%s) OR resp:(%s)" limit 0, %d source' % \
                (text, text, limit)
        logger.debug('BQL: %s' % bql)
        return bql

    def _make_delete_bql(self, id):
        bql = 'delete from LINDEN where id = "%s"' % id
        logger.debug('BQL: %s' % bql)
        return bql

    def _request_search(self, text, limit, cluster, only_post=False):
        bql = self._make_search_bql(text, limit, only_post)
        result = self._rand_client().handleBqlRequest(self.domain, cluster, bql)
        return result

    def _request_delete(self, cluster, id):
        bql = self._make_delete_bql(id)
        result = self._rand_client().handleBqlRequest(self.domain, cluster, bql)
        return result

    def delete(self, cluster, id):
        return self._request_delete(cluster, id)

    def make_index(self, cluster, contents):
        result = self._rand_client().handleIndexRequest(self.domain, cluster, contents)
        return result

    def search(self, query, limit=LIMIT, cluster=CLUSTER, only_post=False):
        request_result = self._request_search(query, limit, cluster, only_post)

        if not request_result.success:
            if request_result.error is not None:
                raise Exception(request_result.error)
            elif request_result.lindenResult is not None:
                raise Exception(request_result.lindenResult.error)
            else:
                raise Exception('Oakbay search error: with nothing')


        top_hits = []
        linden_result = request_result.lindenResult
        logger.debug('Total hits: %d, TOP %s: ' % (limit, linden_result.totalHits))
        for hit in linden_result.hits:
            source = json.loads(hit.source)
            top_hits.append(dict(score=hit.score, source=dict(post=source['post'], resp=source['resp'])))
            logger.debug('%s%s%s%s%s' % (hit.score, SEP, source['post'], SEP, source['resp']))

        result = dict(
            origin_query=query,
            total_hits=linden_result.totalHits,
            limit=limit,
            top_hits=top_hits
        )

        return result

    def search_all(self, cluster, total):
        batch = 10000
        start = 0
        results = []
        while True:
            if start < total:
                bql = 'select * from linden limit %s, %s source' % (start, batch)
                result = self._rand_client().handleBqlRequest(self.domain, cluster, bql)
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
    query = sys.argv[1]
    env = sys.argv[2]
    cluster_name = sys.argv[3]
    client = ConvClient(env, DOMAIN)
    hits = client.search(query, limit=30, cluster=cluster_name)
    client.close()
