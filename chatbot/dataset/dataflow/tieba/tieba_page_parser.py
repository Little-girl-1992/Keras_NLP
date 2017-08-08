#!/usr/bin/env python
# encoding: utf-8

import re
import json
import logging
import html2text
import urlparse
from pyquery import PyQuery as pq

logger = logging.getLogger(__name__)


class CommentParser(object):
    re_reply = re.compile(ur'回复.* :')

    def __init__(self, comment_li_element):
        self.comment_element = comment_li_element
        self.comment_doc = pq(self.comment_element)

    def author(self):
        df = self.comment_element.attrib['data-field']
        username = json.loads(df)['user_name']
        return username

    def id(self):
        df = self.comment_element.attrib['data-field']
        spid = json.loads(df)['spid']
        return spid

    def time(self):
        t = self.comment_doc('.lzl_content_reply')('span.lzl_time')[0].text
        return t

    def text(self):
        t = self.comment_doc('.lzl_cnt')('span.lzl_content_main')[0].text_content()
        t = self.re_reply.sub('', t)
        return t.strip()

    def quote_author(self):
        a = self.comment_doc('.lzl_cnt')('span.lzl_content_main')('a')
        if len(a) != 1:
            return None
        else:
            username = a[0].attrib['username']
            username = urlparse.unquote(username)
            return username

    def parse(self):
        return dict(
            author=self.author(),
            id=self.id(),
            text=self.text(),
            time=self.time(),
            quote_author=self.quote_author()
        )


class PostParser(object):
    re_time = re.compile(r'(\d{4}-\d{1,2}-\d{1,2} \d{2}:\d{2})')

    def __init__(self, post_div_element):
        self.post_element = post_div_element
        self.post_doc = pq(post_div_element)
        self.post_data_filed = json.loads(self.post_element.attrib['data-field'])

    def author(self):
        return self.post_data_filed['author']['user_name']

    def time(self):
        if 'date' in self.post_data_filed['content']:
            return self.post_data_filed['content']['date']
        else:
            text = self.post_doc('.core_reply_tail')[0].text_content()
            m = self.re_time.search(text)
            if m is not None:
                return m.group(0)
            else:
                return None

    def text(self):
        content = self.post_data_filed['content'].get('content', None)
        if not isinstance(content, unicode) or len(content) == 0:
            content = self.post_doc('.p_content')('cc')('div').html()
        try:
            content = html2text.html2text(content)
        except:
            content = self.post_doc('.p_content')('cc')('div')[0].text_content().strip()
        return content

    def id(self):
        return self.post_data_filed['content']['post_id']

    def comment_num(self):
        return self.post_data_filed['content']['comment_num']

    def post_index(self):
        return self.post_data_filed['content']['post_index']

    # will get by /totalComments
    def comments(self):
        lis = self.post_doc('ul')('li.lzl_single_post')
        cs = map(lambda x: CommentParser(x).parse(), lis)
        return cs

    def parse(self):
        return dict(
            author=self.author(),
            time=self.time(),
            id=self.id(),
            text=self.text(),
            post_index=self.post_index()
        )


class MainPageParser(object):
    re_tid = re.compile(r'"thread_id":("\d*?")')
    re_fid = re.compile(r'"forum_id":(\d*?,)')

    def __init__(self, page):
        self.page = page
        self.entire_doc = pq(page)

    def group_id(self):
        group_link = self.entire_doc('#tofrs_up')('a')[0].attrib['href']
        query = urlparse.urlparse(group_link).query
        qs = urlparse.parse_qs(query)
        if 'kw' not in qs or len(qs['kw']) == 0:
            return None
        else:
            kw = qs['kw'][0].decode('utf8')
            return kw

    def topic_id(self):
        tid = None
        rels = self.entire_doc('head')('link')('[rel=canonical]')
        if len(rels) == 1:
            rel_link = rels[0].attrib['href']
            tid = int(rel_link.strip('/').split('/')[-1])
        else:
            m = self.re_tid.search(self.page)
            if m is not None:
                tid = int(m.group(1).strip('"'))
        return tid

    def forum_id(self):
        m = self.re_fid.search(self.page)
        if m is not None:
            fid = int(m.group(1).strip(','))
        else:
            fid = None
        return fid

    def page_info(self):
        paginator = self.entire_doc('.content.clearfix')('.l_posts_num')('li.l_pager.pager_theme_4.pb_list_pager')
        page_links = paginator('a')
        if len(page_links) == 0:
            return {'this_page': 1, 'total_page': 1}
        last_link = page_links[-1].attrib['href']
        last_pn = urlparse.parse_qs(urlparse.urlparse(last_link).query)['pn'][0]
        thispage_element = paginator('span.tP')[0]
        thispage = int(thispage_element.text)
        totalpage = int(last_pn)
        return {'this_page': thispage, 'total_page': totalpage}

    def title(self):
        t = self.entire_doc('.content.clearfix')('.core_title_txt')[0].text
        return t

    def posts(self):
        divs = self.entire_doc('.content.clearfix')('.pb_content')('.p_postlist')('div.l_post.l_post_bright')
        ps = map(lambda x: PostParser(x).parse(), divs)
        return ps

    def parse(self):
        return dict(
            group_id=self.group_id(),
            topic_id=self.topic_id(),
            forum_id=self.forum_id(),
            page_info=self.page_info(),
            title=self.title(),
            posts=self.posts()
        )


class TotalCommentPage(object):
    re_reply = re.compile(ur'回复 \[(.*)\]\(.*\) :')

    def __init__(self, page):
        self.page = page

    def comment(self, c):
        content = c['content']
        content = html2text.html2text(content)
        m = self.re_reply.search(content)
        if m is not None:
            quote_author = m.group(1)
            content = self.re_reply.sub('', content).strip()
        else:
            quote_author = None

        return dict(
            id=int(c['comment_id']),
            author=c['username'],
            quote_author=quote_author,
            content=content,
            tid=int(c['thread_id']),
            pid=int(c['post_id'])
        )

    def parse(self):
        comments = {}
        try:
            page_info = json.loads(self.page)
        except:
            return comments
        if page_info['errno'] != 0:
            return comments
        comment_list = page_info['data']['comment_list']
        if not isinstance(comment_list, dict) or len(comment_list) == 0:
            return comments
        for pid, pidv in comment_list.iteritems():
            comment_info = map(lambda x: self.comment(x), pidv['comment_info'])
            comments[pid] = {'comment_info': comment_info, 'comment_num': pidv['comment_num'],
                             'comment_list_num':pidv['comment_list_num']}
        return comments


class PostCommentPage(object):
    def __init__(self, page):
        self.page = page
        self.entire_doc = pq(page)

    def comments(self):
        lis = self.entire_doc('li.lzl_single_post')
        cs = map(lambda x: CommentParser(x).parse(), lis)
        return cs

    def parse(self):
        return self.comments()



if __name__ == '__main__':
    import sys
    import traceback
    with open(sys.argv[1]) as f:
        with open(sys.argv[2], 'w') as ouf:
            for line in f:
                r = json.loads(line)
                if len(r['res']) < 100*1024:
                    continue
                try:
                   res = MainPageParser(r['res']).parse()
                   ouf.write(('%s\n' % json.dumps(res)).encode('utf8'))
                except Exception as e:
                    print r['url']
                    traceback.print_exc(e)
                    break
