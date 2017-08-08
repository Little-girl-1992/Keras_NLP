#!/usr/bin/env python
# encoding: utf-8

import os
import sys

import pprint
import logging
from elasticsearch import Elasticsearch
from optparse import OptionParser

tools_path = os.path.abspath(os.path.join(os.path.realpath(__file__), '../../tools'))
sys.path.append(tools_path)
from segment import segment

reload(sys)
sys.setdefaultencoding('utf8')
logger = logging.getLogger(__file__)

INDEX = 'chatbot_v2'
LIMIT = 100
AUTH_URL = 'http://elastic:changeme@localhost:9200'


class SearchClient(object):
    """
    client = SearchClient(index='test_index', doc_type='test_type')
    client.search('今天天气不错')
    """

    def __init__(self, index=INDEX, doc_type='', auth_url=AUTH_URL,
                 limit=LIMIT, bigram='no', query_expansion=True):
        """
        index:            数据库名
        doc_type:         为空则检索所有doc_type，否则检索指定doc_type
        auth_url:         自定义es地址
        limit:            返回的结果数量
        bigram:           是否使用bigram，use | no | only
        query_expansion:  查询时是否进行同义词扩展
        """
        self._index = index
        self._doc_type = doc_type
        self._client = Elasticsearch(auth_url)
        self.limit = limit
        self.bigram = bigram
        self.query_expansion = query_expansion
        self.cut = segment

    def make_query_body(self, text):
        if self.query_expansion:
            analyzer = 'chatbot_analyzer_search_v1'
        else:
            analyzer = 'chatbot_analyzer_v1'

        origin_query = {
            'multi_match': {
                'type': 'best_fields',
                'query': text,
                'fields': ['post', 'resp'],
                'analyzer': analyzer
            }
        }
        bigram_query = {
            'multi_match': {
                'type': 'best_fields',
                'query': text,
                'fields': ['post.shingles', 'resp.shingles']
            }
        }

        if self.bigram == 'only':
            body = {'query': bigram_query}
        elif self.bigram == 'no' :
            body = {'query': origin_query}
        else:
            body = {
                'query':{
                    'bool':{
                        'must': origin_query,
                        'should': bigram_query
                    }
                }
            }
        return body

    def query_search(self, text, limit):

        body = self.make_query_body(text)
        logger.debug('Query Body:\n%s\n' % pprint.pformat(body))

        result = self._client.search(
            index=self._index,
            doc_type=self._doc_type,
            body=body,
            size=limit
        )
        return result

    def search(self, query, limit=None, cut_custom=True):
        """
        query: string, 查询字符串
        limit: 返回数量
        """
        if limit is None:
            limit = self.limit

        processed_query = self.cut(query, cut_custom)

        query_result = self.query_search(processed_query, limit)

        hits_result = query_result['hits']
        total_hits = hits_result['total']
        top_hits = []

        logger.debug('Query is: %s' % processed_query)
        for hit in hits_result['hits']:
            source = hit['_source']
            top_hits.append(dict(score=hit['_score'], source=dict(post=source['post'], resp=source['resp'])))
            logger.debug('%s\t%s\t%s | %s' % (hit['_score'], source['src'], source['post'], source['resp']))

        result = dict(
            origin_query=query,
            processed_query=processed_query,
            total_hits=total_hits,
            limit=limit,
            top_hits=top_hits
        )

        return result


if __name__ == '__main__':
    logging.basicConfig(level='DEBUG')
    parser = OptionParser()
    parser.add_option('-q', '--query', help='query string, like "东周列国战国篇"'),
    parser.add_option('-i', '--index', default='chatbot_v2', help='index, like "chatbot"'),
    parser.add_option('-t', '--doc_type', default='', help='doc_type, like "weibo"'),
    parser.add_option('-n', '--limit', default=10, type=int, help='result limit, like 10"'),
    parser.add_option('-b', '--bigram', default='no', help='是否使用bigram：only | use | no')
    parser.set_defaults(query_expansion=True)
    parser.add_option('--nqe', action='store_false', dest='query_expansion', help='not use query expasion')

    options, args = parser.parse_args()

    client = SearchClient(index=options.index, doc_type=options.doc_type, limit=options.limit,
                          bigram=options.bigram, query_expansion=options.query_expansion)

    client.search(options.query)
