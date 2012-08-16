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
    remove_bad_by_attrs(doc)
    remove_bad_by_classifier(doc)

    clean(doc, strip_attrs=False)

    remove_empty_elements(doc)
    doc = unwrap_elements(doc)

    rewrite_links(doc, url)

    return lxml.html.tostring(doc, pretty_print=True)

def remove_empty_elements(doc):
    to_delete = []
    for el in doc.iter():
        # just left those have imgs
        if el.tag == 'img' or el.xpath('.//img'):
            continue
        if not html_to_text(el).strip():
            to_delete.append(el)
    for el in reversed(to_delete):
        if el.getparent() is not None:
            el.drop_tree()

def remove_non_content(doc):
    tags = 'head link style script noscript meta iframe header footer'.split()
    xpath = '|'.join('//' + tag for tag in tags)
    for el in doc.xpath(xpath):
        if el.getparent() is not None:
            el.drop_tree()

def remove_bad_by_classifier(doc):
    ps = justext.justext(
        doc, justext.get_stoplist('English'))
    to_delete = []
    good = []
    for p in ps:
        if p['class'] == 'bad':
            for el in doc.xpath(p['xpath']):
                to_delete.append((el, p['xpath']))
        elif p['class'] == 'good':
            good.append(p['xpath'])

    for el, xp in reversed(to_delete):
        if el.getparent() is not None and not any(xp in g for g in good):
            el.drop_tree()

def remove_bad_by_attrs(doc):
    to_delete = []
    for el in doc.iter():
        if (
            matches_attr(_bad_attr_re, el, 'class', 'id')
            and not any(
                matches_attr(_good_attr_re, x, 'class', 'id')
                for x in el.iter())):
            to_delete.append(el)

    for el in reversed(to_delete):
        if el.getparent() is not None:
            el.drop_tree()

def clean(doc, strip_elements=True, strip_attrs=True):
    """ Clean ``doc`` DOM"""
    to_delete = []
    for el in doc.iter():

        # stript unwanted attrs
        # XXX: should we left height/width for img?
        if strip_attrs:
            for k in el.attrib.keys():
                if (
                    k in ('id', 'style', 'class', 'height', 'width')
                    or k.startswith('data-')):
                    del el.attrib[k]

        # strip text nodes
        if el.tail:
            el.tail = el.tail.strip()
        if el.text:
            el.text = el.text.strip()

def unwrap_elements(doc):

    if doc.tag == 'html' and len(doc) > 0:
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
    'popup',
    '^media$',
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
    'subscri',
    'buy',
    'header',
    '(^|\-|_)date($|\-|_)',
    )

_good_attr_re = gen_matches_any(
    'article',
    'body',
    'content',
    'entry',
    'hentry',
    'main',
    'page',
    'pagination',
    'post',
    'text',
    'blog',
    'story',
    )
