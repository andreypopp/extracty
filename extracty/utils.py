"""

    extracty.utils -- various utilities
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import re
import lxml.html
import dateutil.parser

def gen_matches_any(*p):
    """ Generate regexp for matching against any of the parts ``p``"""
    return re.compile('|'.join('(%s)' % v for v in p), re.I)

def matches_attr(p, e, *attrs):
    """ Check if element ``e`` has any of the ``attrs`` matches ``p``"""
    for attr in attrs:
        if attr in e.attrib and p.search(e.attrib[attr]):
            return True
    return False

def html_to_text(doc):
    """ HTML to text converter"""
    if isinstance(doc, basestring):
        doc = lxml.html.fromstring(doc)

    txt = doc.xpath('.//text()')
    txt = ' '.join(txt)
    return re.sub('\s+', ' ', txt).strip()

def precedings(element, before=None, skip=None):
    """ Traverse tree from element in preceding order

    Order defined as:
        1. traverse preceding siblings
        2. for each sibling traverse chidlren recursively in reverse order
        3. go up to parent and traverse from it starting from 1.

    :param before:
        predicate which will tell traverser to stop
    :param skip:
        predicate to wkip some nodes from traversing

    """

    skip = skip or (lambda x: False)

    def _rev_children(element):
        for e in element.iterchildren(reversed=True):
            if skip(e):
                continue
            for se in _rev_children(e):
                yield se
            yield e

    def _precedings(element):
        for sib in element.itersiblings(preceding=True):
            if skip(sib):
                continue
            for ch in _rev_children(sib):
                yield ch
            yield sib

        if element.getparent() is not None and not skip(element.getparent()):
            yield element.getparent()
            for el in _precedings(element.getparent()):
                yield el

    for x in _precedings(element):
        if before and before(x):
            break
        yield x

def depth_first(element, skip=None):
    """ Traverse tree in depth-first manner"""
    if not (skip and skip(element)):
        yield element
        for ch in element.iterchildren():
            for el in depth_first(ch, skip=skip):
                yield el

def try_parse_timestamp(v):
    try:
        return dateutil.parser.parse(v)
    except ValueError:
        return None
