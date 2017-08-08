#!/usr/bin/env python
# encoding: utf-8

from detect import Detection
from optparse import OptionParser

topk = 1
mark_chars = ['40009', '40010']


def file_line_count(fpath):
    count = 0
    with open(fpath) as f:
        for line in f:
            count += 1
    return count


def fmt_seq2seq_prob_line(line):
    # -2.4421103000641 | 二师兄 叫我 | 40009 师傅 被 妖怪 抓走 了 ！ 40010

    parts = line.split('|')
    if len(parts) != 3:
        return ''

    post = ' '.join(parts[1].split()[::-1])
    resp_words = parts[2].split()
    for c in mark_chars:
        if c in resp_words:
            resp_words.remove(c)
    resp = ' '.join(resp_words)

    post = Detection.format_messy_line(post)
    resp = Detection.format_messy_line(resp)

    # 临时，这一步应在数据清洗时做
    # if Detection.most_repeats(post, 4) or Detection.most_repeats(resp, 4):
    #     return ''

    return '%s | %s\n' % (post, resp)


def main(infile, outfile):
    line_count = file_line_count(infile)
    top_line_count = int(topk * line_count)

    count = 0
    with open(infile) as inf:
        with open(outfile, 'w') as ouf:
            for line in inf:
                count += 1
                if count > top_line_count:
                    break
                line = fmt_seq2seq_prob_line(line)
                ouf.write(line)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-i', '--infile', help='source file')
    parser.add_option('-o', '--outfile', help='segmented file')
    options, args = parser.parse_args()
    main(options.infile, options.outfile)
