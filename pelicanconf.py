#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'cssug'
SITENAME = u'\u4e2d\u56fdSaltStack\u7528\u6237\u7ec4'
SITETITLE = u'\u4e2d\u56fdSaltStack\u7528\u6237\u7ec4'
SITESUBTITLE = u'China SaltStack User Group'
SITEURL = ''

PATH = 'content'

TIMEZONE = 'Asia/Taipei'

DEFAULT_LANG = u'zh'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (('知识库', '/kb/'),
         (u'Salt-Air', '/saltair/'),
         (u'SaltConf', '/saltconf/'),
         (u'About', '/about/'))

# Social widget
SOCIAL = (('github', 'https://github.com/cssug'),
          ('weibo', 'http://weibo.com/saltstack'),
          ('group', 'https://groups.google.com/forum/#!forum/saltstack-users-cn'))

DEFAULT_PAGINATION = 10

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True

DISPLAY_CATEGORIES_ON_MENU = True
CATEGORY_URL = '{slug}/'
CATEGORY_SAVE_AS = '{slug}/index.html'
ARTICLE_URL = '{category}/{slug}/'
ARTICLE_SAVE_AS = '{category}/{slug}/index.html'
PAGE_URL = '{slug}/'
PAGE_SAVE_AS = '{slug}/index.html'

STATIC_PATHS = [
    'images',
    'static']
EXTRA_PATH_METADATA = {
  'static/CNAME': {'path': 'CNAME'}
}

THEME = 'themes/Flex'
SITELOGO = '/images/site_logo.png'

DEFAULT_DATE_FORMAT = '%Y-%m-%d'

