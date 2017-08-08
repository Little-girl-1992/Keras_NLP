#!/usr/bin/env python
# encoding: utf-8

import logging

from comm.clean import CleanData, parse_conv_str, joint_conv_str
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

"""
清洗用于计算覆盖率的query集：
    1. top query
"""


def clean(ustring, len_limit=True):
    if not isinstance(ustring, unicode):
        ustring = ustring.decode('utf8')
    ustring = CleanData.full_2_half_width(ustring)
    if '/:' in ustring:
        return None
    ustring = CleanData.sub_brackets(ustring)
    ustring = CleanData.filter_common_chars(ustring)
    ustring = CleanData.reduce_symbol(ustring)
    ustring = ustring.strip()

    m = CleanData.re_chg.search(ustring)
    if m is None:
        return None

    if CleanData.most_repeats(ustring, 3):
        return None

    if len_limit and not (2 < len(ustring) < 30):
        return None

    return ustring


def deal_file(infile, oufile):
    count = 0
    with open(infile) as inf:
        with open(oufile, 'w') as ouf:
            for line in inf:
                count += 1
                if count % 10000 == 0:
                    logger.info('Has processed %s' % count)
                try:
                    message = line.strip()
                    cleaned_message = clean(message)
                    if cleaned_message is None:
                        continue
                    ouline = cleaned_message
                except Exception as e:
                    logger.exception(e)
                else:
                    ouf.write('%s\n' % ouline.encode('utf8'))
            logger.info('Has processed %s' % count)


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-i', '--infile', help='input file path')
    parser.add_argument('-o', '--oufile', help='output file path')
    args = parser.parse_args()
    deal_file(args.infile, args.oufile)
