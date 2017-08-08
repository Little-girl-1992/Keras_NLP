#!/usr/bin/env python
# encoding: utf-8

import os
import ujson as json
import logging
from collections import defaultdict

from comm.detect import Detection
from comm import clean
logger = logging.getLogger(__file__)


def out_encode(ustring):
    if type(ustring) == unicode:
        ustring = ustring.encode('utf-8')
    return ustring


def replace_line_break(ustring):
    ustring = ustring.replace('\r\n', u'。')
    ustring = ustring.replace('\n', u'。')
    return ustring


def merge_records(records):
    if len(records) == 0:
        return
    records.sort(key=lambda x: x['page_info']['this_page'])
    record = records[0]
    for r in records[1:]:
        record['comments'] += r['comments']
    return record


def extract_quote_comments(record):
    detect = Detection()

    quoted_comments = filter(lambda x: 'quote_comment' in x, record['comments'])
    convs = map(lambda x: (x['quote_comment']['text'], x['text']), quoted_comments)
    convs = filter(lambda x: detect.valid_conv(x), convs)
    return convs


def extract_title_comments(record):
    detect = Detection()

    convs = []

    topic = record['topic']
    title = topic['title']

    if title[-3:] == '...':
        return convs

    if not (detect.valid_len(title) and detect.is_valid(title)):
        return convs

    content = topic['content']
    if u'<图片' in content:
        return convs
    if len(content) > 50:
        return convs
    if detect.re_url_strict.search(content) is not None:
        return convs

    topic_author = topic['author']
    # comments = topic['popular_comments']
    # comments = filter(lambda x: x['vote_count'] > 0, topic['comments'])
    comments = record['comments']
    comments = filter(lambda x: 'quote_comment' not in x, comments)
    comments = filter(lambda x: x['author'] != topic_author, comments)
    comments = sorted(comments, key=lambda x: x['vote_count'], reverse=True)
    comments = map(lambda x: x['text'], comments)
    valid_comments = []
    for comment in comments:
        if len(valid_comments) < 10 and detect.valid_len(comment) and detect.is_valid(comment):
            valid_comments.append(comment)

    for comment in valid_comments:
        conv = [replace_line_break(title), replace_line_break(comment)]
        convs.append(conv)

    return convs


def extract_from_file(inpath, oupath):
    with open(inpath) as f:
        lines = f.readlines()
    structs = map(lambda x: json.loads(x), lines)
    topic_structs = defaultdict(list)
    for struct in structs:
        topic_id = struct['topic_id']
        topic_structs[topic_id].append(struct)

    ouf = open(oupath, 'w')
    for topic_id, records in topic_structs.iteritems():
        merged_record = merge_records(records)
        convs = extract_title_comments(merged_record)
        for conv in convs:
            conv_line = clean.joint_conv_str(conv)
            ouf.write('%s\n' % out_encode(conv_line))
    ouf.close()


def extract_from_dir(indir, outdir):
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    files = os.listdir(indir)
    in_out_paths = map(lambda x: (os.path.join(indir, x), os.path.join(outdir, x)), files)
    for infile, outfile in in_out_paths:
        print 'deal with: %s' % infile
        extract_from_file(infile, outfile)


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-f', '--dealFile', action='store_true', default=False, help='convert struct file to conv file')
    parser.add_argument('-d', '--dealDir', action='store_true', default=False, help='convert struct file dir to conv file dir')
    parser.add_argument('-i', '--inpath', help='input path, filepath for dealFile or dirpath for dealDir')
    parser.add_argument('-o', '--oupath', help='output path, filepath for dealFile or dirpath for dealDir')
    args = parser.parse_args()
    if args.dealFile:
        extract_from_file(args.inpath, args.oupath)
    elif args.dealDir:
        extract_from_dir(args.inpath, args.oupath)
