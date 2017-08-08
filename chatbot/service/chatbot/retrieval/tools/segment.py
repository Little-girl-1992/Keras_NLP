#!/usr/bin/env python
# encoding: utf-8

import re
import os
import jieba
from optparse import OptionParser

"""
分词：
line --> w1 w2 w3 w4 ...
"""

re_eng = re.compile(r'\w[\w\s]+\w')
re_white = re.compile(r'\s+')
dict_path = os.path.abspath(os.path.join(os.path.realpath(__file__),
                                         '../dicts/miui_ad_100w_custome.dict'))

dt_jieba = jieba.dt
dt_custom = jieba.Tokenizer()
dt_custom.load_userdict(dict_path)


def format_messy_line(line):
    TMP_ENG_DELIMITER = '<->'
    engs = re_eng.findall(line)
    for eng in engs:
        tmp_eng = TMP_ENG_DELIMITER.join(eng.split())
        line = line.replace(eng, tmp_eng)
    line = ''.join(line.split())
    line = line.replace(TMP_ENG_DELIMITER, ' ')
    return line


def segment(line, custom=True):
    line = format_messy_line(line)
    if custom:
        words = dt_custom.cut(line)
    else:
        words = dt_jieba.cut(line)
    line = ' '.join(words)
    line = re_white.sub(' ', line)
    return line


def main(infile, outfile):
    with open(infile) as inf:
        with open(outfile, 'w') as outf:
            for line in inf:
                line = segment(line)
                line = line.encode('utf8')
                outf.write(line + '\n')


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-i', '--infile', help='source file')
    parser.add_option('-o', '--outfile', help='segmented file')
    options, args = parser.parse_args()
    main(options.infile, options.outfile)
