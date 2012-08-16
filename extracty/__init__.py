"""

    extracty -- metadata extraction from HTML documents
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This library provides a set of tools to extract various metadata from HTML
    documents, such as title, timestamps, authorship and so on.

"""

import re
import urlparse
import justext
import lxml.html

from .author import extract_author
from .image import extract_cover_image
from .title import extract_title
from .content import extract_content
from .utils import gen_matches_any, html_to_text, precedings, fetch_url

__all__ = (
    'extract', 'extract_author', 'extract_cover_image', 'extract_title',
    'html_to_text')

def extract(doc, url, author=True, cover_image=True, title=True, content=True):
    """ Extract metadata from HTML document"""
    if isinstance(doc, basestring):
        doc = lxml.html.fromstring(doc)

    metadata = {'url': url}

    if author:
        metadata['author'] = extract_author(doc)

    if title:
        metadata['title'] = extract_title(doc)

    if cover_image:
        extracted = extract_cover_image(doc, url)
        if extracted:
            extracted = urlparse.urljoin(url, extracted)
        metadata['cover_image'] = extracted

    # this should go last, because it mutates tree
    if content:
        metadata['content'] = extract_content(doc, url)

    return metadata

def main():
    """usage: extracty [options] SRC

    argument:
        SRC     url or filename

    options:
        -h, --help          show this message and exit
        -u, --url URL       url to use in case of filename provided
        --no-cover-image    do not extract image
        --no-author         do not extract author
        --no-title          do not extract title
    """
    import docopt
    import urllib2
    args = docopt.docopt(main.__doc__)

    if args['SRC'].lower().startswith('http'):
        url = args['SRC']
        data = fetch_url(url)
    else:
        url = args['--url'] or ''
        data = open(args['SRC']).read()
    metadata = extract(data, url=url,
        author=not args['--no-author'],
        title=not args['--no-title'],
        cover_image=not args['--no-cover-image'],
        )
    for k, v in metadata.items():
        v = v or ''
        print '%s\t%s' % (k, v.encode('utf8'))
