#!/usr/bin/env python
# encoding: utf-8


from collections import OrderedDict


class LRU(object):
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = OrderedDict()

    def get(self, k, default=None):
        return self.cache.get(k, default)

    def set(self, k, v):
        if k not in self.cache and len(self.cache) >= self.capacity:
            self.cache.popitem(last=False)
        self.cache[k] = v

    def incr(self, k, v):
        curv = self.get(k, 0)
        tarv = curv + v
        self.set(k, tarv)

