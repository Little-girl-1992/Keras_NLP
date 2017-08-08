#!/usr/bin/env python
# encoding: utf-8

import re
import logging

from comm.clean import CleanData, parse_conv_str, joint_conv_str
logger = logging.getLogger(__name__)


def clean(ustring, len_limit=True):
    if not isinstance(ustring, unicode):
        ustring = ustring.decode('utf8')

    ustring = CleanData.full_2_half_width(ustring)
    ustring = ustring.replace('alink', ' ')
    ustring = CleanData.sub_brackets(ustring)
    ustring = CleanData.filter_common_chars(ustring)
    ustring = CleanData.reduce_symbol(ustring)

    if len_limit and len(ustring) < 5:
        return None
    else:
        return ustring


def clean_conv(conv):
    assert len(conv) == 2
    post = clean(conv[0])
    resp = clean(conv[1])
    if post is None or resp is None:
        return None
    else:
        return [post, resp]


def deal_file(infile, oufile):
    count = 0
    with open(infile) as inf:
        with open(oufile, 'w') as ouf:
            for line in inf:
                count += 1
                if count % 10000 == 0:
                    print 'Has processed %s' % count
                conv = parse_conv_str(line)
                post = clean(conv[0])
                resp = clean(conv[1])
                if post is None or resp is None:
                    continue
                ouline = joint_conv_str([post, resp])
                # ouf.write(line)
                ouf.write('%s\n' % ouline.encode('utf8'))
                # ouf.write('\n')
            print 'Has processed %s' % count


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-i', '--infile', help='input file path')
    parser.add_argument('-o', '--oufile', help='output file path')
    args = parser.parse_args()
    deal_file(args.infile, args.oufile)
