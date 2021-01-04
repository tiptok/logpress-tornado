#!/usr/bin/env python
# coding=utf8
try:
    import psyco
    psyco.full()
except:
    pass
from datetime import datetime
# from lib.markdown import Markdown

# markdowner = Markdown()


def datetimeformat(value, format='%Y-%m-%d %H:%M'):
    return value.strftime(format)


def truncate_words(s, num=50, end_text='...'):
    s = s.encode('utf8')
    length = int(num)
    if len(s) > length:
        s = s[:length]
        if not s[-1].endswith(end_text):
            s = s + end_text
    return s


def mdconvert(value):
    # //return markdowner.convert(value)
    return

def null(value):
    return value if value else ""


def register_filters():
    filters = {}
    filters['truncate_words'] = truncate_words
    filters['datetimeformat'] = datetimeformat
    filters['markdown'] = mdconvert
    filters['null'] = null
    return filters
