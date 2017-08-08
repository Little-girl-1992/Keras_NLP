# coding=utf-8

import json
import urllib2
import unittest
from pprint import pprint


def issue_request(service_endpoint, request_data):
  json_data = json.dumps(request_data)
  req = urllib2.Request(service_endpoint)
  result = urllib2.urlopen(req, json_data)
  response = '\n'.join(result.readlines())
  parsed = json.loads(response)
  return parsed


# run tests by: python tsets.py
class PostTest(unittest.TestCase):
  def setUp(self):
    self.service_endpoint = 'http://dlchat-cnbj2.api.xiaomi.net'

  def test_hello(self):
    response = issue_request(self.service_endpoint, {"user": "lvrr",
                                                     "query": 'i love you',
                                                     "device": "lvrr_device",
                                                     "reply": "i love you so mush",
                                                     "confidence": "confidence",
                                                     "status": "0"})
    pprint(response)


if __name__ == '__main__':
  unittest.main()
