#!/usr/bin/env python
# encoding: utf-8

import logging

from comm.clean import CleanData, parse_conv_str, joint_conv_str
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean(ustring, len_limit=True):
    if not isinstance(ustring, unicode):
        ustring = ustring.decode('utf8')
    ustring = ustring.replace('\r\n', u'。')
    ustring = ustring.replace('\n', u'。')
    ustring = CleanData.full_2_half_width(ustring)
    ustring = CleanData.sub_brackets(ustring)
    ustring = CleanData.filter_common_chars(ustring)
    ustring = CleanData.reduce_symbol(ustring)

    if len_limit and len(ustring) < 3:
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
                    logger.info('Has processed %s' % count)
                try:
                    conv = parse_conv_str(line.strip())
                    cleaned_conv = clean_conv(conv)
                    if cleaned_conv is None:
                        continue
                    ouline = joint_conv_str(cleaned_conv)
                except Exception as e:
                    logger.exception(e)
                else:
                    # ouf.write(line)
                    ouf.write('%s\n' % ouline.encode('utf8'))
                    # ouf.write('\n')
            logger.info('Has processed %s' % count)


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-i', '--infile', help='input file path')
    parser.add_argument('-o', '--oufile', help='output file path')
    args = parser.parse_args()
    deal_file(args.infile, args.oufile)
