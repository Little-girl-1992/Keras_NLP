#!/usr/bin/env python
# encoding: utf-8

import sys
import json
import hashlib
import elasticsearch.helpers
from elasticsearch import Elasticsearch

from optparse import OptionParser

reload(sys)
sys.setdefaultencoding('utf8')

INDEX = 'chatbot_v2'
auth_url = 'http://elastic:changeme@localhost:9200'

es = Elasticsearch(auth_url)


def reindex(source, dest):
    config = {
        'source': {'index': source},
        'dest': {'index': dest}
    }

    es.reindex(body=config, wait_for_completion=False)


def pad_index(i):
    return '%010d' % i


def conv_text(conv):
    keys = conv.keys()
    keys.sort()
    values = [conv[k] for k in keys]
    text = '|'.join(values)
    return text


def conv_id(conv):
    text = conv_text(conv)
    m = hashlib.md5()
    m.update(text)
    id = m.hexdigest()
    return id[16: 32]


def create_indices():
    with open('./index_config.json') as f:
        index_config = json.load(f)

    update_config = {
        'settings': { 'index': { 'number_of_replicas': 0 } }
    }

    es.indices.create(index=INDEX, body=index_config)
    es.indices.put_settings(index=INDEX, body=update_config)


def bulk_index(es, convs, doc_type):
    actions = [
        {'_op_type': 'index', '_index': INDEX, '_type': doc_type, '_source': d, '_id': conv_id(d)}
        for d in convs
    ]
    elasticsearch.helpers.bulk(es, actions, chunk_size=10000)


def index(fpath, src):

    convs = []
    idx = 0
    with open(fpath) as f:
        for line in f:
            idx += 1
            parts = line.split('|')
            post = parts[0].strip()
            resp = parts[1].strip()
            convs.append(dict(post=post, resp=resp, src=src))

            if idx % 10000 == 0:
                bulk_index(es, convs, src)
                convs = []
                print('Has indexed %d convs' % idx)
        bulk_index(es, convs, src)
        print('Has indexed %d convs' % idx)


if __name__ == '__main__':
    parser = OptionParser(usage='usage: %prog [options] arg')
    parser.add_option('-i', '--srcfile', type='string', help='source file')
    parser.add_option('-t', '--srctype', type='string', help='source document type')
    parser.set_defaults(create_indices=False)
    parser.add_option('-c', action='store_true', dest='create_indices',
                      help='create indices by default settings')
    options, args = parser.parse_args()

    if len(sys.argv) < 2:
        parser.print_help()
    elif options.create_indices:
        create_indices()
    else:
        index(options.srcfile, options.srctype)
