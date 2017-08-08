#!/usr/bin/env python
# encoding: utf-8

import re


class Detection(object):
    """
    对米聊数据做合法性判断:
        1. 单句：数字、url、关键词
        2. 整体：100w条语句中每句长度与出现次数的关系
        ** 所有输入的s需要为unicode
    """

    re_eng = re.compile(r'\w[\w\s]+\w')
    re_chg = re.compile(r'[\u4e00-\u9fa5]+')
    re_num = re.compile(r'[\d\-]{6,}')
    # 这个非常慢
    re_url = re.compile(r'(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))')
    re_url_strict = re.compile(r'\w{2,}\.\w{2,3}')
    # 颜文字,所有带括号的都算
    re_kao = re.compile(r'\(|\)|（|）'.decode('utf8'))
    # 表情，所有[yummy!]格式的都算
    re_emoji = re.compile(r'\[[\w|\s|\.\!\?]*\]')
    invalid_str = ['http://', 'https://', 'ftp://', 'www.',
                   u'约不约',
                   u'我和你已经成为好友',
                   u'你的版本过低无法正常显示', u'您的版本不支持', u'你的版本不支持',
                   u'你的版本暂不支持查看',
                   u'收到一条视频消息',
                   u'[系统提示]', u'[图片]', u'[图片消息]', u'[语音消息]' ]
    len_limit = 50
    repeat_limit = 3

    @staticmethod
    def most_repeats(ustring, repeat_limit=None):
        """
            获取最多重复次数的连续重复子串
            repeate_limit不为None，则返回True or False
        """

        length = len(ustring)
        subs = [ustring[i:] for i in range(length)]

        sub = ''
        max_count = 0
        for i in range(0, length):
            for j in range(1, length - i + 1):
                k = j
                count = 1
                while (i + k < length) and (subs[i][: j] == subs[i+k][: j]):
                    count += 1
                    k += j
                if count > max_count:
                    max_count = count
                    sub = subs[i][: j]
                    if repeat_limit is not None and max_count > repeat_limit:
                        return True

        if repeat_limit is not None:
            return max_count > repeat_limit
        else:
            return max_count, sub

    @staticmethod
    def format_messy_line(line):
        TMP_ENG_DELIMITER = '<->'
        engs = Detection.re_eng.findall(line)
        for eng in engs:
            tmp_eng = TMP_ENG_DELIMITER.join(eng.split())
            line = line.replace(eng, tmp_eng)
        line = ''.join(line.split())
        line = line.replace(TMP_ENG_DELIMITER, ' ')
        return line

    @staticmethod
    def strQ2B(ustring):
        """把字符串全角转半角"""
        rstring = ""
        for uchar in ustring:
            inside_code=ord(uchar)
            if inside_code==0x3000:
                inside_code=0x0020
            elif not 0xff01 <= inside_code <= 0xff5e:
                pass
            else:
                inside_code-=0xfee0
            rstring += unichr(inside_code)
        return rstring

    def __init__(self):
        pass

    def is_valid(self, s):

        if len(s) > Detection.len_limit:
            return False

        if '\n' in s:
            return False

        # 转换小写
        s = s.lower()
        # 转换半角
        s = Detection.strQ2B(s)

        # 整理格式
        s = ''.join(s.split())

        for p in Detection.invalid_str:
            if p in s:
                return False

        if Detection.re_num.search(s) is not None:
            return False

        if Detection.re_url_strict.search(s) is not None:
            return False

        if Detection.re_kao.search(s) is not None:
            return False

        repeat_count, substr = Detection.most_repeats(s)
        if repeat_count > Detection.repeat_limit:
            return False

        return True

    def valid_len_count(self, s, c):
        # 去掉emoji表情
        s = Detection.re_emoji.sub('', s)
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
