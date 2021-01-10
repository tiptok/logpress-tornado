#!/usr/bin/env python
# encoding=utf-8
import os

DEBUG = True

SITE_NAME = u'Logpress'
SITE_KEYWORDS = """"""
SITE_DESC = """blog powered by tornado,jinja2,peewee"""
DOMAIN = 'http://127.0.0.1:9000'

THEME_NAME = 'fluid-blue'

DB_ENGINE = 'peewee.MySQLDatabase'  # peewee.SqliteDatabase,peewee.MySQLDatabase
DB_HOST = '127.0.0.1:3306'
DB_USER = 'root'
DB_PASSWD = '123456'
# db file if DB_ENGINE is SqliteDatabase
# DB_NAME = os.path.join(os.path.dirname(__file__), 'blog')
DB_NAME = 'blog'

ADMIN_EMAIL = '594611460@qq.com'
SMTP_SERVER = 'smtp.qq.com'
SMTP_PORT = 587
SMTP_USER = 'noreply@szgeist.com'
SMTP_PASSWORD = 'xxxxxx'
SMTP_USETLS = True
