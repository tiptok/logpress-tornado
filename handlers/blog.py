#!/usr/bin/env python
# coding=utf8
try:
    import psyco
    psyco.full()
except:
    pass
from jinja2  import FileSystemLoader
from handlers import BaseHandler
from models import Post, Category, Tag, Link, Comment
import os
import re
import urllib
from datetime import datetime
from lib.pagination import Pagination
import peewee
from peewee import fn
from peewee import RawQuery
from tornado.web import StaticFileHandler
from core import db


class BlogHandler(BaseHandler):

    @property
    def redis(self):
        return self.application.redis

    def get_recent_posts(self):
        return Post.select().paginate(1, 5)

    def get_random_posts(self):
        if isinstance(db.database, peewee.SqliteDatabase):
            return Post.select().order_by(fn.Random()).limit(5)
        else:
            return Post.select().order_by(fn.Rand()).limit(5)

    def get_category(self):
        return Category.select()

    def get_tagcloud(self):
        return Tag.select(Tag, fn.count(Tag.name).alias('count')).group_by(Tag.name)

    def get_links(self):
        return Link.select()

    def get_archives(self):
        # if isinstance(db.database, peewee.SqliteDatabase):
        #     return RawQuery("select strftime('%Y',created) year,strftime('%m',created) month,count(id) count from posts group by month")
        # elif isinstance(db.database, peewee.MySQLDatabase):
        #     return RawQuery("select date_format(created,'%Y') year,date_format(created,'%m') month,count(id) count from posts group by month",None,_database=db.database)
        return None

    def get_calendar_widget(self):
        pass

    def get_recent_comments(self):
        return Comment.select().order_by(Comment.created.desc()).limit(5)

    def render(self, template_name, **context):
        tpl = '%s/%s' % (self.settings.get('theme_name'), template_name)
        return BaseHandler.render(self, tpl, **context)


class IndexHandler(BlogHandler):

    def get(self, page=1):
        p = self.get_argument('p', None)
        if p:
            post = Post.get(id=int(p))
            post.readnum += 1
            post.save()
            self.render('post.html', post=post)
        else:
            pagination = Pagination(Post.select(), int(page), per_page=8)
            self.render('index.html', pagination=pagination)


class PostHandler(BlogHandler):

    def get(self, postid):
        post = self.get_object_or_404(Post, id=int(postid))
        post.readnum += 1
        post.save()
        author = self.get_cookie('comment_author')
        email = self.get_cookie('comment_email')
        website = self.get_cookie('comment_website')
        self.render('post.html', post=post, comment_author=author,
                    comment_email=email, comment_website=website)


class ArchiveHandler(BlogHandler):

    def get(self, year, month, page=1):
        format = '%%%s-%s%%' % (year, month)
        posts = Post.select().where(Post.created ** format)
        pagination = Pagination(posts, int(page), per_page=8)
        self.render('archive.html',
                    year=year, month=month,
                    pagination=pagination, flag='archives',
                    obj_url='/archives/%s/%s' % (year, month))


class CategoryHandler(BlogHandler):

    def get(self, name, page=1):
        posts = Post.select().join(Category).where(Category.name == name)
        pagination = Pagination(posts, int(page), per_page=8)
        self.render('archive.html', pagination=pagination, name=name,
                    obj_url='/category/%s' % (name), flag='category')


class TagHandler(BlogHandler):

    def get(self, tagname, page=1):
        tags = Tag.select().where(Tag.name == tagname)
        postids = [tag.post for tag in tags]
        pagination = Pagination(Post.select().where(
            Post.id << postids), int(page), per_page=8)
        self.render('archive.html', pagination=pagination,
                    name=tagname, obj_url='/tag/%s' % (tagname), flag='tag')


class FeedHandler(BaseHandler):

    def get(self):
        posts = Post.select().paginate(1, 10)
        self.set_header("Content-Type", "application/atom+xml")
        self.render('feed.xml', posts=posts)


class CommentFeedHandler(BaseHandler):

    def get(self, postid):
        self.set_header("Content-Type", "application/atom+xml")
        post = Post.get(id=int(postid))
        self.render('comment_feed.xml', post=post)

_email_re = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
    # quoted-string
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"'
    r')@(?:[A-Z0-9]+(?:-*[A-Z0-9]+)*\.)+[A-Z]{2,6}$', re.IGNORECASE)

_url_re = re.compile(r'(http://[^/\\]+)', re.I)


class PostCommentHandler(BaseHandler):

    @property
    def mail_connection(self):
        return self.application.email_backend

    def post(self):
        postid = self.get_argument('comment_post_ID')
        author = self.get_argument('author', None)
        email = self.get_argument('email', None)
        url = self.get_argument('url', None)
        comment = self.get_argument('comment', None)
        parent_id = self.get_argument('comment_parent', None)

        if postid:
            post = Post.get(id=int(postid))
            if author and email and comment:
                if len(author) > 18:
                    self.flash('UserName is too long.')
                    return self.redirect("%s#respond" % (post.url))
                if not _email_re.match(email):
                    self.flash(u'Email address is invalid.')
                    return self.redirect("%s#respond" % (post.url))
                if url and not _url_re.match(url):
                    self.flash(u'website is invalid.')
                    return self.redirect("%s#respond" % (post.url))

                comment = Comment.create(post=post, ip=self.request.remote_ip,
                                         author=author, email=email, website=url,
                                         content=comment, parent_id=parent_id)
                self.set_cookie('comment_author', author)
                self.set_cookie('comment_email', email)
                self.set_cookie('comment_website', url)
                return self.redirect(comment.url)
            else:
                self.flash(u"请填写必要信息(姓名和电子邮件和评论内容)")
                return self.redirect("%s#respond" % (post.url))


class SitemapHandler(BaseHandler):

    def get(self):
        self.set_header("Content-Type", "text/xml")
        self.render('sitemap.xml', posts=Post.select(), today=datetime.today())


class BaiduSitemapHandler(BaseHandler):

    def get(self):
        self.set_header("Content-Type", "text/xml")
        self.render('baidu.xml', posts=Post.select())

routes = [
    (r"/", IndexHandler),
    (r'/page/(\d+)', IndexHandler),
    (r'/post/post-(\d+).html', PostHandler),
    (r'/tag/([^/]+)', TagHandler),
    (r'/tag/([^/]+)/(\d+)', TagHandler),
    (r'/category/([^/]+)', CategoryHandler),
    (r'/category/([^/]+)/(\d+)', CategoryHandler),
    (r'/feed', FeedHandler),
    (r'/sitemap.xml', SitemapHandler),
    (r'/baidu.xml', BaiduSitemapHandler),
    (r'/archives/(\d+)/(\d+)', ArchiveHandler),
    (r'/archive/(\d+)/feed', CommentFeedHandler),
    (r'/post/new_comment', PostCommentHandler),
]
