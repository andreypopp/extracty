"""

    extracty -- metadata extraction from HTML documents
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This library provides a set of tools to extract various metadata from HTML
    documents, such as title, timestamps, authorship and so on.

"""

import re
import urlparse
import urllib2
import justext
import lxml.html
import itertools
import Image
from cStringIO import StringIO

from .author import extract_author
from .utils import gen_matches_any, html_to_text, precedings

__all__ = (
    'extract', 'extract_author', 'extract_cover_image',
    'html_to_text')

def extract(doc, url=None, html=False, author=True, cover_image=True):
    """ Extract metadata from HTML document"""
    if isinstance(doc, basestring):
        doc = lxml.html.fromstring(doc)
    metadata = {'url': url}
    if author:
        metadata['author'] = extract_author(doc)
    if cover_image:
        extracted = extract_cover_image(doc, url)
        if extracted:
            extracted = urlparse.urljoin(url, extracted)
        metadata['cover_image'] = extracted

    # this should go last, because it mutates tree
    if html:
        metadata['html'] = extract_html(doc)
    return metadata

def extract_cover_image(doc, url, paragraphs=None, min_image_size=None):
    """ Extract cover image from doc

    :param doc:
        HTML document as a string or as a parsed
    :param min_image_size:
        minimum allowed image size
    """
    if isinstance(doc, basestring):
        doc = lxml.html.fromstring(doc)

    def _find_og_meta_image(doc):
        return
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
                yield content

    def _find_twitter_meta_image(doc):
        return
        metas = doc.xpath('//meta[@name="twitter:image"]')
        for meta in metas:
            if meta.attrib.get('content'):
                yield meta.attrib['content']

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
                yield image

    funcs = (_find_og_meta_image, _find_twitter_meta_image, _find_heueristics)
    for image in itertools.chain(*(f(doc) for f in funcs)):
        image = urlparse.urljoin(url, image)
        if image:
            if min_image_size:
                if isinstance(min_image_size, tuple):
                    (mw, mh) = min_image_size
                else:
                    (mw, mh) = (min_image_size, min_image_size)
                (w, h) = image_size(image)
                if mw is not None and w < mw:
                    continue
                if mh is not None and h < mh:
                    continue
            return image.strip()

def image_size(url):
    data = urllib2.urlopen(url)
    infp = StringIO()
    infp.write(data.read())
    infp.seek(0)
    img = Image.open(infp)
    return img.size

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

_image_urls_banned = gen_matches_any(
    'avatar', '\.gif', '\.ico', 'logo', 'ads')

_image_opengraph_banned = gen_matches_any(
    'opengraph', 'og', 'user', 'logo')

def main():
    """usage: extracty [options] SRC

    argument:
        SRC     url or filename

    options:
        -h, --help          show this message and exit
        -u, --url URL       url to use in case of filename provided
    """
    import docopt
    import urllib2
    args = docopt.docopt(main.__doc__)

    if args['SRC'].lower().startswith('http'):
        request = urllib2.Request(args['SRC'], headers={
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8)'
                ' AppleWebKit/536.25 (KHTML, like Gecko)'
                ' Version/6.0 Safari/536.25')

        })
        data = urllib2.urlopen(request).read()
        url = args['SRC']
    else:
        data = open(args['SRC']).read()
        url = args['--url'] or ''
    metadata = extract(data, url=url)
    for k, v in metadata.items():
        v = v or ''
        print '%s\t%s' % (k, v.encode('utf8'))
