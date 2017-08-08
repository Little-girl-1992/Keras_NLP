#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import json
import hashlib

from client import ConvClient

SEP = ' |<->| '
DOMAIN = 'chatbot'


def conv_text(conv):
    keys = conv.keys()
    keys.sort()
    values = [conv[k] for k in keys]
    text = SEP.join(values)
    return text


def conv_id(conv):
    text = conv_text(conv)
    m = hashlib.md5()
    m.update(text)
    id = m.hexdigest()
    return id[16: 32]


def index(fpath, env, cluster):

    with open(fpath) as f:
        lines = f.readlines()

    contents = []

    for i, line in enumerate(lines):
        parts = line.split(SEP)
        if len(parts) == 2:
            post = parts[0].strip()
            resp = parts[1].strip()
        elif len(parts) == 1:
            post = parts[0].strip()
            resp = 'NULLRESP'
        content = dict(post=post, resp=resp)
        content['id'] = conv_id(content)
        contents.append(json.dumps(content))

    chunks = [contents[x: x+100] for x in xrange(0, len(contents), 100)]

    print('Start index')

    client = ConvClient(env, DOMAIN)
    for i, chunk in enumerate(chunks):
        client.make_index(cluster, chunk)
        print('Has indexed %d convs' % ((i+1) * 100))

    print('Indexed Done for %d convs' % len(contents))

    client.close()


def main(fpath, env, cluster):
    index(fpath, env, cluster)


if __name__ == '__main__':
    fpath = sys.argv[1]
    env = sys.argv[2]
    cluster = sys.argv[3]
    main(fpath, env, cluster)
