#!/usr/bin/env python
# coding=utf-8
try:
    import psyco
    psyco.full()
except:
    pass
import peewee
import datetime
import hashlib
import urllib
from core import db
from lib.helpers import create_token, cached_property
from core import smtp_server, settings
from config import DOMAIN as domain
from playhouse.signals import post_save
from lib.mail.message import TemplateEmailMessage


class User(db.Model):
    username = peewee.CharField()
    password = peewee.CharField()
    email = peewee.CharField()

    @staticmethod
    def create_password(raw):
        salt = create_token(8)
        passwd = '%s%s%s' % (salt, raw, 'blog_engine')
        hsh = hashlib.sha1(passwd.encode('utf-8')).hexdigest()
        return "%s$%s" % (salt, hsh)

    def check_password(self, raw):
        if '$' not in self.password:
            return False
        salt, hsh = self.password.split('$')
        passwd = '%s%s%s' % (salt, raw, 'blog_engine')
        verify = hashlib.sha1(passwd.encode('utf-8')).hexdigest()
        return verify == hsh

    class Meta:
        table_name = 'users'


class Category(db.Model):
    name = peewee.CharField()
    slug = peewee.CharField()

    @property
    def url(self):
        return '/category/%s' % (urllib.quote(self.name.encode('utf8')))

    class Meta:
        table_name = 'category'


class Post(db.Model):
    title = peewee.CharField()
    slug = peewee.CharField(index=True, max_length=100)
    category = peewee.ForeignKeyField(Category, related_name='posts')
    content = peewee.TextField()
    readnum = peewee.IntegerField(default=0)
    tags = peewee.CharField(null=True)
    slug = peewee.CharField(null=True)
    created = peewee.DateTimeField(default=datetime.datetime.now)

    @property
    def url(self):
        return '/post/post-%d.html' % (self.id)

    @property
    def absolute_url(self):
        return '%s%s' % (domain, self.url)

    @property
    def comment_feed(self):
        return '%s/archive/%s/feed' % (domain, self.id)

    @cached_property
    def prev(self):
        posts = Post.select().where(Post.created < self.created)\
            .order_by(Post.created)
        return posts.get() if posts.exists() else None

    @cached_property
    def next(self):
        posts = Post.select().where(Post.created > self.created)\
            .order_by(Post.created)
        return posts.get() if posts.exists() else None

    @property
    def summary(self):
        return self.content.split('<!--more-->')[0] if self.content else self.content

    def taglist(self):
        if self.tags:
            tags = [tag.strip() for tag in self.tags.split(",")]
            return set(tags)
        else:
            return None

    class Meta:
        table_name = "posts"
        order_by = ('-created',)


class Tag(db.Model):
    name = peewee.CharField(max_length=50)
    post = peewee.IntegerField()

    @property
    def url(self):
        return '/tag/%s' % (urllib.quote(self.name.encode('utf8')))


class Comment(db.Model):
    post = peewee.ForeignKeyField(Post, related_name='comments')
    author = peewee.CharField()
    website = peewee.CharField(null=True)
    email = peewee.CharField()
    content = peewee.TextField()
    ip = peewee.TextField()
    parent_id = peewee.IntegerField(null=True)
    created = peewee.DateTimeField(default=datetime.datetime.now)

    @property
    def parent(self):
        p = Comment.select().where(Comment.parent_id == self.parent_id, Comment.id == self.id)
        return p.get() if p.exists() else None

    @property
    def url(self):
        return '%s/post/post-%s.html#comment-%s' % (domain, self.post.id, self.id)

    def gravatar_url(self, size=80):
        return 'http://www.gravatar.com/avatar/%s?d=identicon&s=%d' % \
            (hashlib.md5(self.email.strip().lower().encode('utf-8')).hexdigest(),
             size)

    class Meta:
        table_name = 'comments'


class Link(db.Model):
    name = peewee.CharField()
    url = peewee.CharField()

    class Meta:
        table_name = 'links'



@post_save(sender=Comment)
def send_email(model_class, instance, created):
    if instance.parent_id == '0':
        message = TemplateEmailMessage(u"收到新的评论", 'mail/new_comment.html',
                                       settings['smtp_user'], to=[settings['admin_email']], connection=smtp_server, params={'comment': instance})
    else:
        message = TemplateEmailMessage(u"评论有新的回复", 'mail/reply_comment.html',
                                       settings['smtp_user'], to=[instance.email], connection=smtp_server, params={'comment': instance})
    message.send()
