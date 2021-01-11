from unittest.mock import Mock

import pytest

from sanic import Sanic, headers
from sanic.compat import Header
from sanic.exceptions import PayloadTooLarge
from sanic.http import Http
from sanic.request import Request


@pytest.mark.parametrize(
    "input, expected",
    [
        ("text/plain", ("text/plain", {})),
        ("text/vnd.just.made.this.up ; ", ("text/vnd.just.made.this.up", {})),
        (
            "text/plain;charset=us-ascii",
            ("text/plain", {"charset": "us-ascii"}),
        ),
        (
            'text/plain ; charset="us-ascii"',
            ("text/plain", {"charset": "us-ascii"}),
        ),
        (
            'text/plain ; charset="us-ascii"; another=opt',
            ("text/plain", {"charset": "us-ascii", "another": "opt"}),
        ),
        (
            'attachment; filename="silly.txt"',
            ("attachment", {"filename": "silly.txt"}),
        ),
        (
            'attachment; filename="strange;name"',
            ("attachment", {"filename": "strange;name"}),
        ),
        (
            'attachment; filename="strange;name";size=123;',
            ("attachment", {"filename": "strange;name", "size": "123"}),
        ),
        (
            'form-data; name="files"; filename="fo\\"o;bar\\"',
            ("form-data", {"name": "files", "filename": 'fo"o;bar\\'})
            # cgi.parse_header:
            # ('form-data', {'name': 'files', 'filename': 'fo"o;bar\\'})
            # werkzeug.parse_options_header:
            # ('form-data', {'name': 'files', 'filename': '"fo\\"o', 'bar\\"': None})
        ),
        # <input type=file name="foo&quot;;bar\"> with Unicode filename!
        (
            # Chrome:
            # Content-Disposition: form-data; name="foo%22;bar\"; filename="😀"
            'form-data; name="foo%22;bar\\"; filename="😀"',
            ("form-data", {"name": 'foo";bar\\', "filename": "😀"})
            # cgi: ('form-data', {'name': 'foo%22;bar"; filename="😀'})
            # werkzeug: ('form-data', {'name': 'foo%22;bar"; filename='})
        ),
        (
            # Firefox:
            # Content-Disposition: form-data; name="foo\";bar\"; filename="😀"
            'form-data; name="foo\\";bar\\"; filename="😀"',
            ("form-data", {"name": 'foo";bar\\', "filename": "😀"})
            # cgi: ('form-data', {'name': 'foo";bar"; filename="😀'})
            # werkzeug: ('form-data', {'name': 'foo";bar"; filename='})
        ),
    ],
)
def test_parse_headers(input, expected):
    assert headers.parse_content_header(input) == expected


@pytest.mark.asyncio
async def test_header_size_exceeded():
    recv_buffer = bytearray()

    async def _receive_more():
        nonlocal recv_buffer
        recv_buffer += b"123"

    protocol = Mock()
    http = Http(protocol)
    http._receive_more = _receive_more
    http.request_max_size = 1
    http.recv_buffer = recv_buffer

    with pytest.raises(PayloadTooLarge):
        await http.http1_request_header()
