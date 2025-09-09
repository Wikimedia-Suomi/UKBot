# encoding=utf-8
# vim: fenc=utf-8 et sw=4 ts=4 sts=4 ai
import re

from ..common import _
from ..contributions import UserContribution
from .rule import Rule
from .decorators import family


class ExternalLinkRule(Rule):

    rule_name = 'external_link'

    @staticmethod
    def count_links(txt, contains=None):
        # We don't want to include links in references as these are covered by the RefRule
        txt = re.sub(r'<ref[^>]*>.*?</ref>', '', txt, flags=re.MULTILINE)
        links = re.findall(r'(?<!\[)\[([^\[\] ]+) ([^\[\]]+)\](?!\])', txt)
        if contains:
            contains = contains.lower()
            links = [l for l in links if contains in l[0].lower() or contains in l[1].lower()]
        return len(links)

    @family('wikipedia.org', 'wikibooks.org')
    def test(self, rev):
        contains = self.get_param('contains')
        links_before = self.count_links(rev.parenttext, contains)
        links_after = self.count_links(rev.text, contains)
        links_added = links_after - links_before

        if links_added > 0:
            points = links_added * self.points
            yield UserContribution(rev=rev, points=points, rule=self,
                                   description=_('links') % {'links': links_added})

