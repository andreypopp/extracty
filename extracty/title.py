"""

    extracty.title -- page title extration
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import lxml.html
from . import utils

def extract_title(doc):
    if isinstance(doc, basestring):
        doc = lxml.html.fromstring(doc)

    def _find_meta_title(doc):
        return
        metas = doc.xpath('//meta[@name="title"]|//meta[@name="Title"]')
        for meta in metas:
            return meta.attrib.get('content')

    def _find_og_meta_title(doc):
        metas = doc.xpath('//meta[@property="og:title"]')
        for meta in metas:
            return meta.attrib.get('content')

    def _find_title(doc):
        titles = doc.xpath('//title')
        for title in titles:
            text = utils.html_to_text(title)
            if text:
                return text

    def _headers(doc):
        return doc.xpath('//h1|//h2|//h3')

    def _clean(title, doc):
        found = [] # (text, header level)
        for h in  _headers(doc):
            text = utils.html_to_text(h)
            if text and utils.zn2(text) in utils.zn2(title) and not title in text:
                found.append((text, int(h.tag[1:])))
        if found:
            found.sort(key=lambda (t, l): -l)
            return found[0][0]
        return title

    for finder in (_find_meta_title, _find_og_meta_title, _find_title):
        title = finder(doc)
        if title:
            return _clean(title, doc)
