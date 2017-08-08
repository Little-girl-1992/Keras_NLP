#!/usr/bin/env python
# encoding: utf-8

import sys
from collections import defaultdict, Counter
from optparse import OptionParser

MOST_RESP = 20


def main(infile, outfile, purchase=False):

    with open(infile) as f:
        data = f.read()

    if purchase:
        # purchase 数据的换行为\r\n
        if '\r\n' in data:
            data = data.replace('\n\n')
        convs_lines = data.split('\n\n')
        convs = map(lambda x: x.split('\n'), convs_lines)
    else:
        convs_lines = data.splitlines()
        convs = map(lambda x: x.split(' | ', convs_lines))

    cs = defaultdict(Counter)

    for conv in convs:
        if len(conv) == 2:
            post, resp = conv
            cs[post.strip()].update([resp.strip()])

    target_lines = []
    for post, c in cs.iteritems():
        resps = c.most_common(MOST_RESP)
        resps = [x[0] for x in resps]
        for resp in resps:
            line = '%s | %s\n' % (post, resp)
            target_lines.append(line)

    with open(outfile, 'w') as f:
        f.writelines(target_lines)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-i', '--infile', type='string', help='in file')
    parser.add_option('-o', '--outfile', type='string', help='out file')
    options, args = parser.parse_args()
    main(options.infile, options.outfile)
