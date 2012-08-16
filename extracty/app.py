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

    is_view = environ['PATH_INFO'] == '/view'

    def response(data, status="200 Success"):
        if is_view:
            headers = [('Content-type', 'text/html')]
        else:
            headers = [('Content-type', 'application/json')]
        start_response(str(status), headers)
        return [json.dumps(data)] if not is_view else data

    def error(message):
        msg = {"error": message} if not is_view else message
        return response(msg, status="400 Error")

    def get_result():
        qs = urlparse.parse_qs(environ['QUERY_STRING'])
        if not 'url' in qs:
            return error("missing 'url' parameter")
        kwargs = {}
        for kw in ('cover_image', 'author', 'title'):
            key = 'no_%s' % kw
            if key in qs:
                kwargs[kw] = False
        url = qs['url'][0]
        doc = fetch_url(url)
        return extract(doc, url, **kwargs)

    result = get_result()
    return response(result) if not is_view else response(template % result)

template = """
<!doctype html>
<style>
    .author, .url {
        font-size: %%80;
        color: #666;
    }
</style>
<div>
    <div class="author">%(author)s</div>
    <div class="url">%(url)s</div>
    <img src="%(cover_image)s">
    <h1 class="title">%(title)s</h1>
    <div class="content">%(content)s</div>
</div>
"""
