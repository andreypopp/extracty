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

from .author import extract_author
from .image import extract_cover_image
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
