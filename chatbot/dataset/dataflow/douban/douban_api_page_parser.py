#!/usr/bin/env python
# encoding: utf-8

import os
import copy
import math
import ujson as json


def api_topic_page_2_struct(topic, group_id):
    intopic = dict(
        id=topic['id'],
        author=topic['author']['id'],
        time=topic['updated'],
        title=topic['title'],
        content=topic['content'],
        like_count=topic['like_count']
    )
    page_info = dict(
        this_page=0,
        total_page=int(math.ceil(topic['comments_count'] / 20.0))
    )
    p = dict(
        group_id=group_id,
        topic_id=topic['id'],
        page_info=page_info,
        topic=intopic,
        comments=[],
        popular_comments=[]
    )
    return p


def api_comment_2_struct_comment(comment):
    c = copy.copy(comment)
    c['author'] = c['author']['id']
    if 'quote_comment' in c:
        c['quote_comment'] = api_comment_2_struct_comment(c['quote_comment'])
    return c


def api_comment_page_2_struct(c, group_id):
    page_info = dict(
        this_page = c.get('start', 0) / 20 + 1,
        total_page = int(math.ceil(c.get('total', 0) / 20.0))
    )
    comments = map(lambda x: api_comment_2_struct_comment(x), c['comments'])
    popular_comments = map(lambda x: api_comment_2_struct_comment(x), c['popular_comments'])
    p = dict(
        group_id=group_id,
        topic_id=c['topic_id'],
        page_info=page_info,
        comments=comments,
        popular_comments=popular_comments
    )
    return p


def api_page_2_struct(page, group_id):
    d = page
    if d['label'] == 'topics':
        topics = d['topics']
        page_structs = map(lambda x: api_topic_page_2_struct(x, group_id), topics)
    elif d['label'] == 'comments':
        page_structs = [api_comment_page_2_struct(d, group_id)]
    else:
        page_structs = []
    return page_structs


def extract_group_file_struct(infile, outfile):
    with open(infile) as f:
        lines = f.readlines()
    group_id = infile.split('/')[-1]
    structs = []
    for line in lines:
        try:
            page = json.loads(line)
        except:
            continue
        else:
            structs += api_page_2_struct(page, group_id)

    with open(outfile, 'w') as f:
        for struct in structs:
            f.write(json.dumps(struct) + '\n')


def convert_whole_dir(indir, outdir):
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    files = os.listdir(indir)
    in_out_paths = map(lambda x: (os.path.join(indir, x), os.path.join(outdir, x)), files)
    for infile, outfile in in_out_paths:
        print 'deal with: %s' % infile
        extract_group_file_struct(infile, outfile)
