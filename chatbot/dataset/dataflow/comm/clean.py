#!/usr/bin/env python
# encoding: utf-8

import re


SEP = ' |<->| '


def joint_conv_str(conv):
    """
    将[post, resp]形式的对话格式化为"post |<->| resp"
    :param conv: list of str, [post, resp]
    :return: type str
    """
    assert len(conv) == 2
    conv[0] = conv[0].strip()
    conv[1] = conv[1].strip()
    return SEP.join(conv)


def parse_conv_str(s):
    """
    将　"post |<->| 转为 [post, resp]"
    :param s: str
    :return: list of str
    """
    conv = s.split(SEP)
    assert len(conv) == 2
    conv[0] = conv[0].strip()
    conv[1] = conv[1].strip()
    return conv


class CleanData(object):
    # 常用字符，半角状态下中文、英文、数字、空白、常用中英文符号
    re_comm = re.compile(ur'([\u4e00-\u9fa5\sa-zA-Z0-9,.?!:/\'"…、，。？！：‘’“”《》]+)')
    # 非常用字符
    re_non_comm = re.compile(ur'([^\u4e00-\u9fa5\sa-zA-Z0-9,.?!:/\'"…、，。？！：‘’“”《》]+)')
    # 只包含半角状态下中文、英文、数字、空格
    re_word = re.compile(ur'([\u4e00-\u9fa5\sa-zA-Z0-9]+)')
    # 非word
    re_non_word = re.compile(ur'([^\u4e00-\u9fa5\sa-zA-Z0-9]+)')
    # 非word，且不是空格
    re_non_strict_word = re.compile(ur'([^\u4e00-\u9fa5a-zA-Z0-9]+)')
    # emoji unicode，并不等同于微博/米聊/...表情
    # 其实utf8范围为\u0000-\uffff，所以通过s.decode('utf8')得到的unicode并不会包含emoji
    re_emoji = re.compile(ur'\u1f601-\u1f64')
    # 颜文字，所有带括号的都算 ！！！
    re_kao = re.compile(ur'\(|\)|（|）')
    # 表情，所有[yummy!]格式的都算，米聊是这种格式
    re_biaoqing = re.compile(ur'\[[\u4e00-\u9fa5\w\s\.\!\?]*\]')
    # 英文及空格
    re_eng = re.compile(ur'\w[\w\s]+\w')
    re_chg = re.compile(ur'[\u4e00-\u9fa5]+')
    re_num = re.compile(ur'[\d\-]{6,}')

    stop_words = {
        u'与', u'个', u'么', u'乎', u'了', u'但', u'兮', u'及', u'可', u'和',
        u'地', u'得', u'或', u'是', u'的', u'矣', u'等', u'而',
    }

    re_brackets = map(
        lambda x: re.compile(x),
        [
            ur'\(.*?\)',
            ur'\[.*?\]',
            ur'\{.*?\}',
            ur'\#.*?\#',
            ur'\\.*?\/',
            ur'\【.*?\】',
            ur'\「.*?\」',
            ur'\『.*?\』',
        ]
    )

    @staticmethod
    def sub_brackets(ustring):
        for m in CleanData.re_brackets:
            ustring = m.sub(' ', ustring)
        return ustring

    @staticmethod
    def full_2_half_width(ustring, excludes=None):
        """
        字符串全角转半角
        :param ustring: type unicode, 如果不是unicode，会默认以utf-8解码
        :param excludes: set of unicode, excludes 中的字符不参与转换, 如果不设置，默认使用 {u'，', u'？', u'！', u'：'}
        :return: type unicode
        """
        if not isinstance(excludes, set):
            excludes = {u'，', u'？', u'！', u'：'}

        rstring = ''
        for uchar in ustring:
            if uchar in excludes:
                rstring += uchar
                continue
            inside_code = ord(uchar)
            if inside_code == 0x3000:
                inside_code = 0x0020
            elif not 0xff01 <= inside_code <= 0xff5e:
                pass
            else:
                inside_code -= 0xfee0
            rstring += unichr(inside_code)
        return rstring

    @staticmethod
    def is_common(us, use_stop_words=False):
        """
        判断一个字符串是否全为常用字符
        :param us: unicode，若为str则默认以utf8解码 
        :param use_stop_words: stop words 当做非常用字符
        :return: 
        """
        if not isinstance(us, unicode):
            us = us.decode('utf-8')

        if use_stop_words and us in CleanData.stop_words:
            return False

        m = CleanData.re_non_comm.search(us)
        if m is not None:
            return False

        return True

    @staticmethod
    def is_word(us, use_stop_words=False):
        """
        判断一个字符串是否全为word
        :param us: unicode，若为str则默认以utf8解码 
        :param use_stop_words: stop words 当做非常用字符
        :return: 
        """
        if not isinstance(us, unicode):
            us = us.decode('utf-8')

        if use_stop_words and us in CleanData.stop_words:
            return False

        m = CleanData.re_non_word.search(us)
        if m is not None:
            return False

        return True

    @staticmethod
    def _filter_replace(filter_func, s, rs=' '):
        if filter_func(s):
            return s
        else:
            return rs

    @staticmethod
    def filter_common_chars(ws, use_stop_words=False):
        """
        过滤出常用字符，若为list，返回过滤后的list，若为unicode str返回过滤后的unicode str
        :param ws: list of unicode, or unicode str,  
        :param use_stop_words: bool
        :return: list or str
        """
        # new_ws = filter(lambda x: CleanData.is_common(x, use_stop_words), ws)
        new_ws = map(lambda x: CleanData._filter_replace(CleanData.is_common, x), ws)
        if isinstance(ws, unicode):
            return ''.join(new_ws)
        return new_ws

    @staticmethod
    def filter_words(ws, use_stop_words=False):
        """
        过滤出word，若为list，返回过滤后的list，若为unicode str返回过滤后的unicode str
        :param ws: list of unicode, or unicode str,  
        :param use_stop_words: bool
        :return: list or str
        """
        # new_ws = filter(lambda x: CleanData.is_word(x, use_stop_words), ws)
        new_ws = map(lambda x: CleanData._filter_replace(CleanData.is_word, x), ws)
        if isinstance(ws, unicode):
            return ''.join(new_ws)
        return new_ws

    @staticmethod
    def most_repeats(ustring, repeat_limit=None):
        """
        获取最多重复次数的连续重复子串
        :param ustring: unicode string, 若为str，则默认以utf8解码 
        :param repeat_limit: None or int，若为int，则返回 True or False，表示最多重复字数是否超过 repeat_limit
        :return: (max_count, sub)，最多重复次数及重复子串 
        """

        if not isinstance(ustring, unicode):
            ustring = ustring.decode('utf-8')

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
    def reduce_symbol(ustring, even_diff=False):
        """
        压缩字符串中的符号，包括空格
        你好呀,呵呵呵。。。。 -> 你好呀,呵呵呵。
        :param ustring: 
        :param even_diff: 如果置为True，只要连续多个符号，无论是否相同，都会略过后续符号
        :return: 
        """
        if len(ustring) == 0:
            return ustring

        if not isinstance(ustring, unicode):
            ustring = ustring.decode('utf8')

        rs = ustring[0]
        last_symbol = CleanData.re_non_strict_word.search(rs) is not None
        for uchar in ustring[1:]:
            now_symbol = CleanData.re_non_strict_word.search(uchar) is not None

            if even_diff:
                if not(now_symbol and last_symbol):
                    rs += uchar
                    last_symbol = now_symbol
            else:
                if not (now_symbol and uchar == rs[-1]):
                    rs += uchar
                    last_symbol = now_symbol

        return rs

    @staticmethod
    def format_messy_line(line):
        """
        压缩字符串的空白符，不包括英文中的
        :param line: unicode string 
        :return: unicode string
        """
        TMP_ENG_DELIMITER = '|<->|'
        engs = CleanData.re_eng.findall(line)
        for eng in engs:
            tmp_eng = TMP_ENG_DELIMITER.join(eng.split())
            line = line.replace(eng, tmp_eng)
        line = ''.join(line.split())
        line = line.replace(TMP_ENG_DELIMITER, ' ')
        return line
