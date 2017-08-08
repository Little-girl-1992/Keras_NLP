#!/usr/bin/env python
# encoding: utf-8

import re
import json
import logging
import html2text
from pyquery import PyQuery as pq

logger = logging.getLogger(__name__)


class CommentsVotesParser(object):
    re_votes = re.compile(r'var commentsVotes = \'(.*)\',')

    @staticmethod
    def get_votes(s):
        votes = CommentsVotesParser.re_votes.findall(s)
        if len(votes) != 1:
            votes = {}
        else:
            votes = json.loads(votes[0])
            votes = {k[1:]: v for k, v in votes.iteritems()}
        return votes


class CommentParser(object):
    def __init__(self, comment_li_element, votes=None):
        self.comment_doc = pq(comment_li_element)
        self.votes = votes

    def author(self):
        author_link = self.comment_doc('.bg-img-green')('h4')('a')[0].attrib['href']
        return author_link.strip('/').split('/')[-1]

    def time(self):
        time = self.comment_doc('.bg-img-green')('h4')('.pubtime')[0].text
        return time

    def quote_comment(self):
        if len(self.comment_doc('.reply-quote')) != 1:
            return None

        text = self.comment_doc('.reply-quote')('.all')[0].text
        author_link = self.comment_doc('.reply-quote')('.pubdate')('a')[0].attrib['href']
        author = author_link.strip('/').split('/')[-1]
        return {'text': text, 'author': author}

    def text(self):
        text = self.comment_doc('p').html()
        return html2text.html2text(text)

    def id(self):
        return self.comment_doc[0].attrib['id']

    def vote_count(self, id):
        if self.votes is None or id not in self.votes:
            return -1
        else:
            return self.votes[id]

    def parse(self):
        try:
            id = self.id()
            c = dict(
                id=id,
                time=self.time(),
                author=self.author(),
                text=self.text(),
                vote_count=self.vote_count(id)
            )
            qc = self.quote_comment()
            if qc is not None:
                c['quote_comment'] = qc
        except:
            c = None
        return c


class TopicParser(object):
    re_topic_like_count = re.compile(ur'(\d+)人')

    def __init__(self, entire_doc):
        self.entire_doc = entire_doc
        self.topic_doc = self._topic_doc()

    def _topic_doc(self):
        return self.entire_doc('#content')('.topic-content')('.topic-doc')

    def author(self):
        author_link = self.topic_doc('h3')('.from')('a')[0].attrib['href']
        return author_link.strip('/').split('/')[-1]

    def time(self):
        update_time = self.topic_doc('h3')('.color-green')[0].text
        return update_time

    def content(self):
        contents = self.topic_doc('.topic-content')
        if len(contents) != 1:
            return ''
        else:
            content = contents.html()
            return html2text.html2text(content)

    def title(self):
        items = self.entire_doc('#content')('.infobox')('.tablecc')
        if len(items) == 1:
            t = html2text.html2text(items[0].text_content()).strip()
            t = t[3:].strip()
        else:
            items = self.entire_doc('#content')('h1')
            t = html2text.html2text(items[0].text_content()).strip()
        return t

    def like_count(self):
        like_link = self.entire_doc('#content')('.topic-content')('.sns-bar-fav')('.fav-num')('a')
        if len(like_link) != 1:
            return -1
        text = like_link[0].text
        counts = self.re_topic_like_count.findall(text)
        if len(counts) != 1:
            count = -1
        else:
            count = int(counts[0])
        return count

    def parse(self):
        return dict(
            author=self.author(),
            time=self.time(),
            title=self.title(),
            content=self.content(),
            like_count=self.like_count()
        )


class TopicPageParser(object):
    def __init__(self, page):
        self.page = page
        self.entire_doc = pq(page)
        self.comment_votes = CommentsVotesParser.get_votes(page)

    def popular_comments(self):
        popular_doc = self.entire_doc('.topic-reply.popular-bd')('li')
        popular_comments = map(lambda x: CommentParser(x, self.comment_votes).parse(), popular_doc)
        popular_comments = filter(lambda x: x is not None, popular_comments)
        return popular_comments

    def comments(self):
        comments_doc = self.entire_doc('.topic-reply#comments')('li')
        comments = map(lambda x: CommentParser(x, self.comment_votes).parse(), comments_doc)
        comments = filter(lambda x: x is not None, comments)
        return comments

    def group_id(self):
        group_link = self.entire_doc('#content')('.aside')('.group-item')('.title')('a')[0].attrib['href']
        return group_link.split('/')[-2]

    def topic_id(self):
        resp_link = self.entire_doc('#content')('#reviews')('a')[0].attrib['href']
        return resp_link.split('/')[-2]

    def page_info(self):
        paginator = self.entire_doc('#content')('.paginator')
        if len(paginator) == 0:
            return {'this_page': 1, 'total_page': 1}
        else:
            thispage_element = paginator('.thispage')[0]
            thispage = int(thispage_element.text)
            totalpage = int(thispage_element.attrib['data-total-page'])
            return {'this_page': thispage, 'total_page': totalpage}

    def _topic_doc(self):
        return self.entire_doc('#content')('.topic-content')('.topic-doc')

    def parse(self):
        if len(self.entire_doc('#wrapper')('#content')('h1')) != 1:
            return None

        try:
            group_id = self.group_id()
            topic_id = self.topic_id()
            page_info = self.page_info()
        except Exception as e:
            logger.warn(e)
            return None

        p = dict(
            group_id=group_id,
            topic_id=topic_id,
            page_info=page_info,
            comments=self.comments(),
            popular_comments=self.popular_comments()
        )

        topic_doc = self._topic_doc()
        if len(topic_doc) == 1:
            topic = TopicParser(self.entire_doc).parse()
            topic['id'] = topic_id
            p['topic'] = topic

        return p
