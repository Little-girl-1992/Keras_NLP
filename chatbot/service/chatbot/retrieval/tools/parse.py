#!/usr/bin/env python
# encoding: utf-8


import sys
import numpy as np
import datetime
import itertools
import ujson as json
from detect import Detection
from optparse import OptionParser
from collections import Counter


THREAD_ID = 'threadId'
TIMESTAMP = 'timestamp'
MSG = 'msg'

dtfmt = '%Y-%m-%d %H:%M:%S'
conv_interval = 30 # 30s
chunck_limit = 1000000


def ts_differ(convs):
    ts = [x['timestamp'] / 1000.0 for x in convs]
    if len(ts) < 2:
        return []
    tss = np.array(ts[: -1])
    tse = np.array(ts[1: ])
    tsd = tse - tss
    return tsd

def extract_conv_pair(convs):
    tsd = ts_differ(convs)
    idxs = np.argwhere(tsd < conv_interval)
    idxs = flatten(idxs)

    pairs = map(lambda i: (convs[i], convs[i+1]), idxs)
    pairs = filter(lambda pair: pair[0]['sent'] != pair[1]['sent'], pairs)

    return pairs


def flatten(l):
    return list(itertools.chain.from_iterable(l))


def parse_1m(convs):
    detection = Detection()

    # 获取去重后的msg及数量
    msgs = [x[MSG] for x in convs]
    msgs = Counter(msgs)
    msgs = msgs.most_common(len(msgs))

    # 获取过滤后的msg
    msgs_filter = filter(lambda x: detection.valid_len_count(x[0], x[1]), msgs)
    msgs_filter = filter(lambda x: detection.is_valid(x[0]), msgs_filter)
    msgs_filter = set([x[0] for x in msgs_filter])

    # 获取分好组的thread
    gconvs = itertools.groupby(convs, lambda x: x[THREAD_ID])
    gconvs = [(idx, list(g)) for idx, g in gconvs]
    gconvs = [sorted(gconv[1], key=lambda x: x['timestamp']) for gconv in gconvs]

    # 获取conv pair，根据上下文的时间间隔
    gconv_pairs = map(lambda x: extract_conv_pair(x), gconvs)
    conv_pairs = flatten(gconv_pairs)

    # 获取msg合法的conv pair
    conv_pairs_filter = filter(lambda x: x[0][MSG] in msgs_filter and x[1][MSG] in msgs_filter, conv_pairs)

    return conv_pairs_filter


def format_flush(conv_pairs, outf):
    def format_msg(conv):
        # dt = datetime.datetime.fromtimestamp(conv[TIMESTAMP] / 1000.0)
        # return '%s\t%s\n' % (dt.strftime(dtfmt), ' '.join(conv[MSG].split()))
        return '%s' % (' '.join(conv[MSG].split()))

    def format_pair(pair):
        return '%s | %s' % (format_msg(pair[0]), format_msg(pair[1]))

    pair_lines = map(lambda x: format_pair(x), conv_pairs)
    outlines = '\n'.join(pair_lines)

    outf.writelines(outlines.encode('utf8'))
    outf.writelines('\n')


def main(infile, outfile):
    convs_1m = []
    count = 0
    with open(outfile, 'w') as outf:
        with open(infile) as inf:
            for line in inf:
                conv = json.loads(line)
                if len(convs_1m) < chunck_limit:
                    convs_1m.append(conv)
                elif conv[THREAD_ID] == convs_1m[-1][THREAD_ID]:
                    convs_1m.append(conv)
                else:
                    conv_pairs = parse_1m(convs_1m)
                    format_flush(conv_pairs, outf)
                    convs_1m = []
                    count += 1
                    print 'Has Processed %d lines' % (count * chunck_limit)
            conv_pairs = parse_1m(convs_1m)
            format_flush(conv_pairs, outf)
            convs_1m = []


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-i', '--infile', help='source file')
    parser.add_option('-o', '--outfile', help='parsed file')
    options, args = parser.parse_args()
    main(options.infile, options.outfile)
