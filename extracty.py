"""

    extracty -- metadata extraction from HTML documents
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This library provides a set of tools to extract various metadata from HTML
    documents, such as title, timestamps, authorship and so on.

"""

import re
import justext
import lxml.html

__all__ = (
    'extract', 'extract_author', 'extract_cover_image',
    'html_to_text')

def extract(doc, html=False, author=True, cover_image=True):
    """ Extract metadata from HTML document"""
    if isinstance(doc, basestring):
        doc = lxml.html.fromstring(doc)
    metadata = {}
    if author:
        metadata['author'] = extract_author(doc)
    if cover_image:
        metadata['cover_image'] = extract_cover_image(doc)

    # this should go last, because it mutates tree
    if html:
        metadata['html'] = extract_html(doc)
    return metadata

def extract_cover_image(doc, paragraphs=None):
    """ Extract cover image from doc

    :param doc:
        HTML document as a string or as a parsed
    """
    if isinstance(doc, basestring):
        doc = lxml.html.fromstring(doc)

    def _find_og_meta_image(doc):
        metas = doc.xpath('//meta[@property="og:image"]')
        if metas:
            # some open graph submitted images can be too generic, try to filter
            # them
            for meta in metas:
                if not meta.attrib.get('content'):
                    continue
                content = meta.attrib['content']
                if _image_opengraph_banned.search(content):
                    continue
                return content

    def _find_twitter_meta_image(doc):
        metas = doc.xpath('//meta[@name="twitter:image"]')
        if metas and metas[0].attrib.get('content'):
            return metas[0].attrib['content']

    def _find_heueristics(doc):
        ps = paragraphs or justext.justext(
            doc, justext.get_stoplist('English'))
        prev = None
        images = []
        tree = lxml.etree.ElementTree(doc)
        for p in ps:
            if p['class'] == 'good':
                xpath = p['xpath']
                e = doc.xpath(xpath)
                if not e:
                    continue
                e = e[0]
                for prec in precedings(e, lambda x: prev is not None and prev is e):
                    if prec.tag == 'img' and prec.attrib.get('src'):
                        images.append(prec.attrib['src'])
                prev = e

        if images:
            for image in images:
                if _image_urls_banned.search(image):
                    continue
                return image

    for finder in (_find_og_meta_image, _find_twitter_meta_image,
            _find_heueristics):
        img = finder(doc)
        if img:
            return img.strip()

def extract_author(doc):
    """ Extract author from ``doc``

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

def extract_html(doc, paragraphs=None):
    if isinstance(doc, basestring):
        doc = lxml.html.fromstring(doc)

    ps = paragraphs or justext.justext(
        doc, justext.get_stoplist('English'))
    for p in ps:
        if p['class'] != 'bad':
            for el in doc.xpath(p['xpath']):
                el.drop_tree()
    return lxml.html.tostring(doc)

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

def precedings(element, before=None):
    """ Traverse preceding elements in tree"""

    if before and before(element):
        yield None
        raise StopIteration()

    def _rev_children(element):
        for e in element.iterchildren(reversed=True):
            for se in _rev_children(e):
                yield se
            yield e

    for sib in element.itersiblings(preceding=True):
        if before and before(sib):
            yield None
            raise StopIteration()
        for ch in _rev_children(sib):
            if before and before(ch):
                yield None
                raise StopIteration()
            yield ch

    if element.getparent() is not None:
        for el in precedings(element.getparent()):
            if el is None or before and before(el):
                yield None
                raise StopIteration()
            yield el

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

_image_urls_banned = gen_matches_any(
    'avatar', '\.gif', '\.ico', 'logo', 'ads')

_image_opengraph_banned = gen_matches_any(
    'opengraph', 'og', 'user', 'logo')

def main():
    import sys
    import urllib2
    args = sys.argv[1:]
    if not args:
        print >> sys.stderr, 'error: provide URL or FILENAME as an argument'
        exit(1)
    if args[0].lower().startswith('http'):
        request = urllib2.Request(args[0], headers={
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8)'
                ' AppleWebKit/536.25 (KHTML, like Gecko)'
                ' Version/6.0 Safari/536.25')

        })
        data = urllib2.urlopen(request).read()
    else:
        data = open(args[0]).read()
    metadata = extract(data)
    for k, v in metadata.items():
        v = v or ''
        print '%s\t%s' % (k, v.encode('utf8'))
