#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import hashlib
from optparse import OptionParser


"""
将单轮对话特大文件，分割成多个小文件，
同时保证同一post在同一文件中，以便后续去重处理
post\nresp\n\n --> post | resp\n
"""


HASH_NUM = 20


class HashFile(object):
    def __init__(self, n):
        self._n = n

    def _md5(self, k):
        m = hashlib.md5()
        m.update(k)
        return m.hexdigest()

    def open(self, outdir):
        self._fs = []
        self._outdir = outdir
        for i in range(self._n):
            fpath = os.path.join(self._outdir, 'part_%s' % i)
            f = open(fpath, 'w')
            self._fs.append(f)

    def get(self, k):
        if type(k) != int:
            k = str(k)
            k = self._md5(k)
            k = int(k, 16)
        fd = k % self._n
        return self._fs[fd]

    def close(self):
        for f in self._fs:
            f.close()


class Conv(object):
    def __init__(self, post=None, resp=None):
        self.post = post
        self.resp = resp

    def clear(self):
        self.__init__()

    def valid(self):
        if self.post is None or self.resp is None:
            return False
        else:
            return True

    def to1line(self):
        return '%s | %s\n' % (self.post, self.resp)

    def valid_1line(self):
        if self.valid():
            return self.to1line()
        else:
            return None


def main(infile, outdir):
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    hf = HashFile(HASH_NUM)
    hf.open(outdir)

    conv = Conv()
    f = open(infile)
    for line in f:
        if line == '\n':
            outline = conv.valid_1line()
            if outline is not None:
                hf.get(conv.post).write(outline)
            conv.clear()
        elif conv.post is None:
            conv.post = line.strip()
        else:
            conv.resp = line.strip()

    f.close()
    hf.close()


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-i', '--infile', help='in file')
    parser.add_option('-o', '--outdir', help='out dir')
    options, args = parser.parse_args()
    main(options.infile, options.outdir)
