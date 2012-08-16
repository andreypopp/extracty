"""

    extracty.content -- content extraction
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import lxml.html
import lxml.builder
import urlparse
import justext

from .utils import html_to_text, gen_matches_any, matches_attr

__all__ = ('extract_content',)

def extract_content(doc, url, html=True):
    """ Extract content from ``doc``

    :param doc:
        HTML as a string or as ElementTree node
    :param url:
        URL of a document
    :param html:
        if we need to return HTML (default to true)
    """
    if isinstance(doc, basestring):
        doc = lxml.html.fromstring(doc)
    remove_non_content(doc)
    remove_bad_by_classifier(doc)
    remove_empty_elements(doc)
    rewrite_links(doc, url)
    clean(doc)
    doc = unwrap_elements(doc)
    return lxml.html.tostring(doc, pretty_print=True)

def remove_empty_elements(doc):
    to_delete = []
    for el in doc.iter():
        if el.tag == 'img' or el.xpath('.//img'):
            continue
        if not html_to_text(el).strip():
            to_delete.append(el)
    for el in reversed(to_delete):
        el.drop_tree()

def remove_non_content(doc):
    tags = 'head link style script noscript meta iframe'.split()
    xpath = '|'.join('//' + tag for tag in tags)
    for el in doc.xpath(xpath):
        el.drop_tree()

def remove_bad_by_classifier(doc):
    ps = justext.justext(
        doc, justext.get_stoplist('English'))
    to_delete = []
    for p in ps:
        if p['class'] == 'bad':
            for el in doc.xpath(p['xpath']):
                to_delete.append(el)
    for el in reversed(to_delete):
        el.drop_tree()

def clean(doc):
    to_delete = []
    for el in doc.iter():
        if matches_attr(_bad_attr_re, el, 'class', 'id'):
            to_delete.append(el)
        for attr in ('id', 'style', 'class'):
            if attr in el.attrib:
                del el.attrib[attr]
        if el.tail:
            el.tail = el.tail.strip()
        if el.text:
            el.text = el.text.strip()
    for el in reversed(to_delete):
        el.drop_tree()

def unwrap_elements(doc):

    if doc.tag == 'html':
        return unwrap_elements(doc[0])
    elif doc.tag in ('body', 'div'):
        if doc.text or doc.tail:
            return doc
        if len(doc) == 1:
            return unwrap_elements(doc[0])
        else:
            return lxml.builder.E.div(*doc)


    return doc

def rewrite_links(doc, url):
    for link in doc.xpath('//a|//img'):
        if link.attrib.get('href'):
            link.attrib['href'] = urlparse.urljoin(url, link.attrib['href'])
        if link.attrib.get('src'):
            link.attrib['src'] = urlparse.urljoin(url, link.attrib['src'])

_bad_attr_re = gen_matches_any(
    'combx',
    'comment',
    'com-',
    'contact',
    'foot',
    'footer',
    'footnote',
    'masthead',
    'media',
    'meta',
    'outbrain',
    'promo',
    'related',
    'scroll',
    'shoutbox',
    'sponsor',
    'shopping',
    'tags',
    'tool',
    'widget',
    'print',
    'comment',
    'taxonom',
    'discuss',
    'e[\-]?mail',
    'share',
    'reply',
    'login',
    'sign',
    'caption',
    'ad-',
    'sidebar',
    'tweet',
    'subscrib',
    'subscript',
    'buy',
    '(^|\-|_)date($|\-|_)',
    )
