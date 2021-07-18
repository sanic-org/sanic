from unittest.mock import Mock

import pytest

from sanic import headers, text
from sanic.exceptions import InvalidHeader, PayloadTooLarge
from sanic.http import Http


@pytest.fixture
def raised_ceiling():
    Http.HEADER_CEILING = 32_768
    yield
    Http.HEADER_CEILING = 16_384


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
    Http.set_header_max_size(1)
    http = Http(protocol)
    http._receive_more = _receive_more
    http.recv_buffer = recv_buffer

    with pytest.raises(PayloadTooLarge):
        await http.http1_request_header()


@pytest.mark.asyncio
async def test_header_size_increased_okay():
    recv_buffer = bytearray()

    async def _receive_more():
        nonlocal recv_buffer
        recv_buffer += b"123"

    protocol = Mock()
    Http.set_header_max_size(12_288)
    http = Http(protocol)
    http._receive_more = _receive_more
    http.recv_buffer = recv_buffer

    with pytest.raises(PayloadTooLarge):
        await http.http1_request_header()

    assert len(recv_buffer) == 12_291


@pytest.mark.asyncio
async def test_header_size_exceeded_maxed_out():
    recv_buffer = bytearray()

    async def _receive_more():
        nonlocal recv_buffer
        recv_buffer += b"123"

    protocol = Mock()
    Http.set_header_max_size(18_432)
    http = Http(protocol)
    http._receive_more = _receive_more
    http.recv_buffer = recv_buffer

    with pytest.raises(PayloadTooLarge):
        await http.http1_request_header()

    assert len(recv_buffer) == 16_389


@pytest.mark.asyncio
async def test_header_size_exceeded_raised_ceiling(raised_ceiling):
    recv_buffer = bytearray()

    async def _receive_more():
        nonlocal recv_buffer
        recv_buffer += b"123"

    protocol = Mock()
    http = Http(protocol)
    Http.set_header_max_size(65_536)
    http._receive_more = _receive_more
    http.recv_buffer = recv_buffer

    with pytest.raises(PayloadTooLarge):
        await http.http1_request_header()

    assert len(recv_buffer) == 32_772


def test_raw_headers(app):
    app.route("/")(lambda _: text(""))
    request, _ = app.test_client.get(
        "/",
        headers={
            "FOO": "bar",
            "Host": "example.com",
            "User-Agent": "Sanic-Testing",
        },
    )

    assert request.raw_headers == (
        b"Host: example.com\r\nAccept: */*\r\nAccept-Encoding: gzip, "
        b"deflate\r\nConnection: keep-alive\r\nUser-Agent: "
        b"Sanic-Testing\r\nFOO: bar"
    )


def test_request_line(app):
    app.route("/")(lambda _: text(""))
    request, _ = app.test_client.get(
        "/",
        headers={
            "FOO": "bar",
            "Host": "example.com",
            "User-Agent": "Sanic-Testing",
        },
    )

    assert request.request_line == b"GET / HTTP/1.1"


@pytest.mark.parametrize(
    "raw",
    (
        "show/first, show/second",
        "show/*, show/first",
        "*/*, show/first",
        "*/*, show/*",
        "other/*; q=0.1, show/*; q=0.2",
        "show/first; q=0.5, show/second; q=0.5",
        "show/first; foo=bar, show/second; foo=bar",
        "show/second, show/first; foo=bar",
        "show/second; q=0.5, show/first; foo=bar; q=0.5",
        "show/second; q=0.5, show/first; q=1.0",
        "show/first, show/second; q=1.0",
    ),
)
def test_parse_accept_ordered_okay(raw):
    ordered = headers.parse_accept(raw)
    expected_subtype = (
        "*" if all(q.subtype.is_wildcard for q in ordered) else "first"
    )
    assert ordered[0].type_ == "show"
    assert ordered[0].subtype == expected_subtype


@pytest.mark.parametrize(
    "raw",
    (
        "missing",
        "missing/",
        "/missing",
    ),
)
def test_bad_accept(raw):
    with pytest.raises(InvalidHeader):
        headers.parse_accept(raw)


def test_empty_accept():
    assert headers.parse_accept("") == []


def test_wildcard_accept_set_ok():
    accept = headers.parse_accept("*/*")[0]
    assert accept.type_.is_wildcard
    assert accept.subtype.is_wildcard

    accept = headers.parse_accept("foo/bar")[0]
    assert not accept.type_.is_wildcard
    assert not accept.subtype.is_wildcard
