#!/usr/bin/env python
# encoding: utf-8

import re
from clean import CleanData


class Detection(CleanData):
    """
    对数据做合法性判断:
        1. 单句：数字、url、关键词
        2. 整体：100w条语句中每句长度与出现次数的关系
        ** 所有输入的s需要为unicode
    """

    # 这个非常非常慢 !!!
    re_url = re.compile(r'(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)'
                        r'(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)'
                        r'|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))')
    re_url_strict = re.compile(r'\w{2,}\.\w{2,3}')
    invalid_str = ['http://', 'https://', 'ftp://', 'www.',
                   '@',
                   u'<图片', u'集合贴', u'求票',
                   u'邮箱', u'已发', u'已收', u'关注', u'豆邮',
                   u'楼上', u'ls',
                   u'加我', u'「',
                  ]
    len_limit = 50
    repeat_limit = 4

    def __init__(self):
        pass

    def is_valid(self, s):

        if len(s) > Detection.len_limit:
            return False

        # 转换小写
        s = s.lower()
        # 转换半角
        s = Detection.full_2_half_width(s)
        # 整理格式
        s = ''.join(s.split())

        for p in Detection.invalid_str:
            if p in s:
                return False

        if Detection.re_num.search(s) is not None:
            return False

        if Detection.re_url_strict.search(s) is not None:
            return False

        # if Detection.re_biaoqing.search(s) is not None:
        #     return False

        repeat_count, substr = Detection.most_repeats(s)
        if repeat_count > Detection.repeat_limit:
            return False

        return True

    def valid_len_count(self, s, c):
        # 去掉emoji
        s = Detection.re_emoji.sub('', s)
        # 去掉表情
        s = Detection.re_biaoqing.sub('', s)
        n = len(s)
        if n < 5:
            return False
        if 5 <= n < 15 and c >= 10:
            return False
        if 15 <= n < 30 and c >= 2:
            return False
        if n >= 30:
            return False
        return True

    def valid_len(self, s):
        s = Detection.re_emoji.sub('', s)
        s = Detection.re_biaoqing.sub('', s)
        n = len(s)
        if n < 5:
            return False
        if n > 30:
            return False
        return True

    def valid_conv(self, conv):
        return self.valid_len(conv[0]) and self.valid_len(conv[1]) and self.is_valid(conv[0]) and self.is_valid(conv[1])
