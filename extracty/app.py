"""

    extracty.server -- HTTP interface to extracty
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import urlparse
try:
    import simplejson as json
except ImportError:
    import json

from . import extract
from .utils import fetch_url

__all__ = ('application',)

def application(environ, start_response):
    """ WSGI application"""
    def response(data, status=200, headers=[]):
        start_response(status, headers)
        return [json.dumps(data)]

    def error(message):
        return response({"error": message}, status=400)

    qs = urlparse.parse_qs(environ['QUERY_STRING'])
    if not 'url' in qs:
        return error("missing 'url' parameter")
    kwargs = {}
    for kw in ('cover_image', 'author', 'title'):
        key = 'no_%s' % kw
        if key in qs:
            kwargs[kw] = False
    url = qs['url']
    doc = fetch_url(url)
    result = extract(doc, url, **kwargs)
    return response(result)
