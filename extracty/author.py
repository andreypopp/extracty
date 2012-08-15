"""

    extracty.author -- extract authorship
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import re
import lxml.html
from .utils import gen_matches_any, html_to_text, matches_attr

__all__ = ('extract_author',)

def extract_author(doc):
    """ Extract authorship from ``doc``

    :param doc:
        HTML document as a string or as a parsed
    """

    if isinstance(doc, basestring):
        doc = lxml.html.fromstring(doc)

    def _find_meta(doc):
        """ Inspect <meta> tags"""
        for name in ('author', 'blogger', 'creator', 'publisher'):
            metas = doc.xpath('//meta[@name="%s"]' % name)
            for meta in metas:
                text = meta.attrib.get('content')

                if not text:
                    continue

                # some publishers like to include domain name here
                if re.search(r'\.[a-z]{2,4}$', text, re.I):
                    continue

                return text

    def _find_itemprop(doc):
        """ Inspect HTML5 itemprop microdata"""
        es = doc.xpath('//*[@itemprop="author"]')
        for e in es:
            text = html_to_text(e)
            if text:
                return text

    def _find_rel(doc):
        """ Inspect rel attributes"""
        es = doc.xpath('//*[@rel="author"]')
        for e in es:
            text = html_to_text(e)
            if text:
                return text

    def _find_heueristics(doc):
        """ Use heueristics to find author in HTML

        Use either id and class names or content itself
        """

        # holds (text, textparts) pairs
        seen = []

        for e in doc.iter():

            text = html_to_text(e)
            found = False

            # if we encounter comments - skip entire tree after that
            if matches_attr(_comment_classes, e, 'class', 'id'):
                break

            if len(text) > 80:
                continue

            # try to match by content
            if _author_content.search(text) or _author_content_2.search(text):
                found = True

            # try to match by class and id names
            if (
                matches_attr(_author_classes, e, 'class', 'id')
                and not matches_attr(_author_classes_banned, e, 'class', 'id')):
                if not text:
                    continue
                found = True

            if found:
                # check if this element specialize its parent
                for (el, _) in seen[:]:
                    if text in el:
                        seen.remove((el, _))
                seen.append((text, list(e.itertext())))

        if seen:
            return seen[0]

    def _best_part(parts):
        parts = parts[:]
        for part in parts[:]:
            if not part or not part.strip():
                parts.remove(part)
            elif re.search(r'[0-9]', part):
                parts.remove(part)
            elif not re.sub(r'[^a-z]+', '', part, flags=re.I):
                parts.remove(part)
        if parts:
            return parts[0]

    def _clean(author, parts):
        if parts:
            parts = [p.strip() for p in parts if p and p.strip() and len(p) > 1]
            author = ' , '.join(parts)
        author = re.sub(r'.*by($|\s)', '', author, flags=re.I)
        author = re.sub(r'^[^a-z]+', '', author, flags=re.I)
        splitter = re.compile(r'( at )|( on )|[,\|]', re.I)
        if splitter.search(author):
            parts = splitter.split(author)
            author = _best_part(parts)
        return author.strip() if author else None

    for finder in (_find_itemprop, _find_meta, _find_heueristics, _find_rel):
        maybe_author = finder(doc)
        if maybe_author is not None:
            if isinstance(maybe_author, tuple):
                text, parts = maybe_author
                return _clean(text, parts)
            else:
                return _clean(maybe_author, None)

_author_classes = gen_matches_any(
    'contributor',
    'author',
    'writer',
    'byline',
    'by$',
    'signoff'
    )

_author_classes_banned = gen_matches_any(
    'date',
    'photo',
    'title',
    'tag',
    )

_comment_classes = gen_matches_any(
    'comment', 'discus', 'disqus', 'pingback')

_author_content = re.compile(
    r'^[^a-z]*(posted)|(written)|(publsihed)|(created)\s?by\s?.+', re.I | re.VERBOSE)

_author_content_2 = re.compile(
    r'^[^a-z]*by\s?.+', re.I | re.VERBOSE)
