# encoding=utf-8
import re
from collections import OrderedDict
import unittest
from unittest.mock import Mock
from unittest import TestCase

import itertools

from ukbot.filters import CatFilter, ExternalLinksFilter
from ukbot.site import Site
from ukbot.sites import SiteManager


def _name_generator():
    for i in itertools.count(1):
        yield f'Name{i}'


class _Faker:
    def __init__(self):
        self._gen = _name_generator()

    def name(self):
        return next(self._gen)


fake = _Faker()


class DummyDataProvider:

    def page_mock(self, name=None, site=None, prefix=''):
        """ Create a MWClient Page instance mock """
        page = Mock()
        page.site = site or self.site
        page.name = '%s%s' % (prefix, name or fake.name())
        return page

    def article_mock(self, name=None, site=None):
        """ Create an UKBOt Article instance mock """
        article = Mock()
        article.site = Mock(return_value=site or self.site)
        article.name = name or fake.name()
        article.key = article.site().key + ':' + article.name
        return article

    def __init__(self, articles: int, categories: int):

        # Define a dummy site
        self.site = Mock(Site)
        self.site.key = 'dummy.wikipedia.org'
        # self.site.redirect_regexp = re.compile(u'(?:%s)' % u'|'.join(['redirect']), re.I)
        self.site.rights = ['bot']

        # And a site manager
        self.sites = Mock(SiteManager)
        self.sites.keys = Mock(return_value=[self.site.key])
        self.sites.items = Mock(return_value=[(self.site.key, self.site)])

        # Create some articles and categories
        self.articles = [self.article_mock() for n in range(articles)]
        self.categories = [self.page_mock(prefix='Kategori:') for n in range(categories)]
        self.articles_keyed = OrderedDict(((article.key, article) for article in self.articles))

    def a_key(self, nr):
        return self.articles[nr].key

    def c_key(self, nr):
        return '%s:%s' % (self.categories[nr].site.key, self.categories[nr].name)


class TestCatFilter(TestCase):

    @staticmethod
    def cat_filter_with_cache(dummy: DummyDataProvider, tree: dict, categories: list = [], maxdepth: int = 5):
        cat_filter = CatFilter(sites=dummy.sites, categories=categories, maxdepth=maxdepth)
        cat_filter.categories_cache = {dummy.site.key: {k.name: {vv.name for vv in v} for k, v in tree.items()}}
        return cat_filter

    @classmethod
    def filter_and_return_keys(cls, dummy: DummyDataProvider, **kwargs):
        cat_filter = cls.cat_filter_with_cache(dummy, **kwargs)
        return list(cat_filter.filter(dummy.articles_keyed).keys())

    def test_simple_filter(self):
        dummy = DummyDataProvider(articles=2, categories=3)

        filtered = self.filter_and_return_keys(dummy=dummy, categories=[dummy.categories[1]], tree={
            dummy.articles[0]: {dummy.categories[0]},
            dummy.articles[1]: {dummy.categories[1]},
            dummy.categories[0]: {},
            dummy.categories[1]: {},
        })

        assert filtered == [dummy.articles[1].key]
        assert dummy.articles[1].cat_path == [dummy.c_key(1)]

    def test_deep_filter(self):
        dummy = DummyDataProvider(articles=3, categories=10)

        filtered = self.filter_and_return_keys(dummy=dummy, categories=[dummy.categories[9]], tree={
            dummy.articles[0]: {dummy.categories[3], dummy.categories[4]},
            dummy.categories[3]: {},
            dummy.categories[4]: {dummy.categories[8]},
            dummy.categories[8]: {dummy.categories[9]},
            dummy.categories[9]: {},
            dummy.articles[1]: {dummy.categories[3], dummy.categories[6]},
            dummy.categories[6]: {},
            dummy.articles[2]: {},
        })

        assert filtered == [dummy.articles[0].key]
        assert dummy.articles[0].cat_path == [dummy.c_key(9), dummy.c_key(8), dummy.c_key(4)]

    def test_maxdepth(self):
        dummy = DummyDataProvider(articles=1, categories=10)

        def kwargs(maxdepth):
            return {
                'dummy': dummy,
                'tree': {
                    dummy.articles[0]: {dummy.categories[0]},
                    dummy.categories[0]: {dummy.categories[1]},
                    dummy.categories[1]: {dummy.categories[2]},
                    dummy.categories[2]: {dummy.categories[3]},
                    dummy.categories[3]: {},
                },
                'categories': [dummy.categories[3]],
                'maxdepth': maxdepth,
            }

        assert self.filter_and_return_keys(**kwargs(2)) == []
        assert self.filter_and_return_keys(**kwargs(3)) == [dummy.a_key(0)]


class TestExternalLinksFilter(TestCase):

    def test_filter(self):
        dummy = DummyDataProvider(articles=3, categories=0)
        dummy.articles[0].name = 'Page1'
        dummy.articles[1].name = 'Page2'
        dummy.articles[2].name = 'Page3'
        for article in dummy.articles:
            article.key = f"{dummy.site.key}:{article.name}"
        dummy.articles_keyed = OrderedDict((a.key, a) for a in dummy.articles)

        dummy.site.api = Mock(return_value={
            'query': {
                'exturlusage': [
                    {'title': dummy.articles[0].name},
                    {'title': dummy.articles[2].name},
                ]
            }
        })

        ext_filter = ExternalLinksFilter(sites=dummy.sites, url='https://example.com')
        filtered = ext_filter.filter(dummy.articles_keyed)
        assert list(filtered.keys()) == [dummy.articles[0].key, dummy.articles[2].key]


if __name__ == '__main__':
    unittest.main()
