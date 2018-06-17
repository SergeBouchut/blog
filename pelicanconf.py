#!/usr/bin/env python
# coding: utf-8
from __future__ import unicode_literals


AUTHOR = u'Serge Bouchut'
SITENAME = u'terrarium'
SITEURL = 'https://sergebouchut.github.io/blog'

PATH = 'content'

TIMEZONE = 'Europe/Paris'

DEFAULT_LANG = u'fr'

# Feed generation is usually not desired when developing
FEED_DOMAIN = SITEURL
FEED_ALL_ATOM = None
FEED_ALL_RSS = 'feeds/rss.xml'
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (
    ('Pelican', 'http://getpelican.com/'),
    ('Python.org', 'http://python.org/'),
    ('Jinja2', 'http://jinja.pocoo.org/'),
)

# Social widget
SOCIAL = (
    ('github', 'https://github.com/SergeBouchut/'),
    ('linkedin', 'https://www.linkedin.com/in/sergebouchut/'),
    ('email', 'serge.bouchut+blog@gmail.com'),
    ('meetup', 'https://www.meetup.com/fr-FR/members/190950919/'),
)

DEFAULT_PAGINATION = 10

# Uncomment following line if you want document-relative URLs when developing
# RELATIVE_URLS = True

THEME = 'pelican-hyde'
PROFILE_IMAGE = 'profile.png'
BIO = (u"Ingénieur logiciel #python #linux, Lyon. "
       u"N\'hésitez pas à laisser des commentaires pour me compléter, "
       u"me corriger, me poser des questions ou simplement m\'encourager ! :)")
DISQUS_SITENAME = u'sergebouchut'
