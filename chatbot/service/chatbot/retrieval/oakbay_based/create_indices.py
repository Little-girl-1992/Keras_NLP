#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import json
import hashlib

from OakbayClient import OakbayClient

DOMAIN = 'chatbot'
CLUSTER = 'chatbot-hot-query'

SEP = ' |<->| '


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


def make_index(client, contents):
  result = client.handleIndexRequest(DOMAIN, CLUSTER, contents)
  return result


def index(fpath, env):
  oakbay_client = OakbayClient(env, 3000)
  finagle_client = oakbay_client.get_client()
  client = finagle_client.get()

  with open(fpath) as f:
    lines = f.readlines()

  contents = []

  for i, line in enumerate(lines):
    parts = line.split(SEP)
    post = parts[0].strip()
    resp = parts[1].strip()
    # post = line.strip()
    # resp = 'NULLRESP'
    content = dict(post=post, resp=resp)
    content['id'] = conv_id(content)
    contents.append(json.dumps(content))

  chunks = [contents[x: x + 100] for x in xrange(0, len(contents), 100)]

  for i, chunk in enumerate(chunks):
    make_index(client, chunk)
    print('Has indexed %d convs' % ((i + 1) * 100))

  print('Indexed Done for %d convs' % len(contents))
  for k, v in oakbay_client.clients.iteritems():
    v.close()
  oakbay_client.close()


def main(fpath, env, cluster):
  global CLUSTER
  CLUSTER = cluster
  print(fpath, env, DOMAIN, CLUSTER)
  index(fpath, env)


if __name__ == '__main__':
  fpath = sys.argv[1]
  env = sys.argv[2]
  cluster = sys.argv[3]
  main(fpath, env, cluster)
