import unittest
from unittest.mock import patch

from ukbot.sites import init_sites


class DummySite:
    def __init__(self, host, prefixes, **kwargs):
        self.host = host
        self.name = host
        self.key = host
        self.prefixes = prefixes
        self.logged_in = True
        self.interwikimap = {
            'en': 'en.wikipedia.org',
            'de': 'de.wikipedia.org',
            'fr': 'fr.wikipedia.org',
            'meta': 'meta.wikimedia.org',
        }
        self.pages = {}


class TestInitSites(unittest.TestCase):
    @patch('ukbot.sites.db_conn')
    @patch('ukbot.sites.fetch_interwikimap')
    @patch('ukbot.sites.Site', new=DummySite)
    def test_othersites_wildcard(self, mock_fetch, mock_db_conn):
        mock_fetch.return_value = {
            'en': 'en.wikipedia.org',
            'de': 'de.wikipedia.org',
            'fr': 'fr.wikipedia.org',
            'meta': 'meta.wikimedia.org',
        }
        config = {
            'homesite': 'en.wikipedia.org',
            'othersites': ['*.wikipedia.org']
        }
        manager, sql = init_sites(config)

        self.assertIn('en.wikipedia.org', manager.sites)
        self.assertIn('de.wikipedia.org', manager.sites)
        self.assertIn('fr.wikipedia.org', manager.sites)
        self.assertNotIn('meta.wikimedia.org', manager.sites)
        self.assertNotIn('*.wikipedia.org', manager.sites)
        mock_db_conn.assert_called_once()


if __name__ == '__main__':
    unittest.main()
