"""

    extracty.image -- images extraction
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import itertools
import urllib2
import urlparse
from cStringIO import StringIO

import lxml.html
import justext
import Image

from . import utils

__all__ = ('extract_cover_image',)

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
                for prec in utils.precedings(e,
                        before=lambda x: prev is not None and prev is e):
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

_image_urls_banned = utils.gen_matches_any(
    'avatar', '\.gif', '\.ico', 'logo', 'ads')

_image_opengraph_banned = utils.gen_matches_any(
    'opengraph', 'og', 'user', 'logo')

