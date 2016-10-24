import re
import os
from zlib import adler32
import mimetypes

from sanic.response import HTTPResponse


def setup(app, dirname, url_prefix):
    @app.middleware
    async def static_middleware(request):
        url = request.url
        if url.startswith(url_prefix):
            filename = url[len(url_prefix):]
            if filename:
                filename = secure_filename(filename)
                filename = os.path.join(dirname, filename)
                if os.path.isfile(filename):
                    return sendfile(filename)


_split = re.compile(r'[\0%s]' % re.escape(''.join(
    [os.path.sep, os.path.altsep or ''])))


def secure_filename(path):
    return _split.sub('', path)


def sendfile(location, mimetype=None, add_etags=True):
    headers = {}
    filename = os.path.split(location)[-1]

    with open(location, 'rb') as ins_file:
        out_stream = ins_file.read()

    if add_etags:
        headers['ETag'] = '{}-{}-{}'.format(
            int(os.path.getmtime(location)),
            hex(os.path.getsize(location)),
            adler32(location.encode('utf-8')) & 0xffffffff)

    mimetype = mimetype or mimetypes.guess_type(filename)[0] or 'text/plain'

    return HTTPResponse(status=200,
                        headers=headers,
                        content_type=mimetype,
                        body_bytes=out_stream)
