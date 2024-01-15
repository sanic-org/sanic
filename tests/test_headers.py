from unittest.mock import Mock

import pytest

from sanic import Sanic, headers, json, text
from sanic.exceptions import InvalidHeader, PayloadTooLarge
from sanic.http import Http
from sanic.request import Request


def make_request(headers) -> Request:
    return Request(b"/", headers, "1.1", "GET", None, None)


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
            'form-data; name="foo"; value="%22\\%0D%0A"',
            ("form-data", {"name": "foo", "value": '"\\\n'}),
        ),
        # <input type=file name="foo&quot;;bar\"> with Unicode filename!
        (
            # Chrome, Firefox:
            # Content-Disposition: form-data; name="foo%22;bar\"; filename="😀"
            'form-data; name="foo%22;bar\\"; filename="😀"',
            ("form-data", {"name": 'foo";bar\\', "filename": "😀"}),
            # cgi: ('form-data', {'name': 'foo%22;bar"; filename="😀'})
            # werkzeug (pre 2.3.0): (
            #   'form-data', {'name': 'foo%22;bar"; filename='}
            # )
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

    assert b"Host: example.com" in request.raw_headers
    assert b"Accept: */*" in request.raw_headers
    assert b"Accept-Encoding: gzip, deflate" in request.raw_headers
    assert b"Connection: keep-alive" in request.raw_headers
    assert b"User-Agent: Sanic-Testing" in request.raw_headers
    assert b"FOO: bar" in request.raw_headers


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
    "raw,expected_subtype",
    (
        ("show/first, show/second", "first"),
        ("show/*, show/first", "first"),
        ("*/*, show/first", "first"),
        ("*/*, show/*", "*"),
        ("other/*; q=0.1, show/*; q=0.2", "*"),
        ("show/first; q=0.5, show/second; q=0.5", "first"),
        ("show/first; foo=bar, show/second; foo=bar", "first"),
        ("show/second, show/first; foo=bar", "first"),
        ("show/second; q=0.5, show/first; foo=bar; q=0.5", "first"),
        ("show/second; q=0.5, show/first; q=1.0", "first"),
        ("show/first, show/second; q=1.0", "second"),
    ),
)
def test_parse_accept_ordered_okay(raw, expected_subtype):
    ordered = headers.parse_accept(raw)
    assert ordered[0].type == "show"
    assert ordered[0].subtype == expected_subtype


@pytest.mark.parametrize(
    "raw",
    (
        "missing",
        "missing/",
        "/missing",
        "/",
    ),
)
def test_bad_accept(raw):
    with pytest.raises(InvalidHeader):
        headers.parse_accept(raw)


def test_empty_accept():
    a = headers.parse_accept("")
    assert a == []
    assert not a.match("*/*")


def test_wildcard_accept_set_ok():
    accept = headers.parse_accept("*/*")[0]
    assert accept.type == "*"
    assert accept.subtype == "*"
    assert accept.has_wildcard

    accept = headers.parse_accept("foo/*")[0]
    assert accept.type == "foo"
    assert accept.subtype == "*"
    assert accept.has_wildcard

    accept = headers.parse_accept("foo/bar")[0]
    assert accept.type == "foo"
    assert accept.subtype == "bar"
    assert not accept.has_wildcard


def test_accept_parsed_against_str():
    accept = headers.Matched.parse("foo/bar")
    assert accept == "foo/bar; q=0.1"


def test_media_type_matching():
    assert headers.MediaType("foo", "bar").match(
        headers.MediaType("foo", "bar")
    )
    assert headers.MediaType("foo", "bar").match("foo/bar")


@pytest.mark.parametrize(
    "value,other,outcome",
    (
        # ALLOW BOTH
        ("foo/bar", "foo/bar", True),
        ("foo/bar", headers.Matched.parse("foo/bar"), True),
        ("foo/bar", "foo/*", True),
        ("foo/bar", headers.Matched.parse("foo/*"), True),
        ("foo/bar", "*/*", True),
        ("foo/bar", headers.Matched.parse("*/*"), True),
        ("foo/*", "foo/bar", True),
        ("foo/*", headers.Matched.parse("foo/bar"), True),
        ("foo/*", "foo/*", True),
        ("foo/*", headers.Matched.parse("foo/*"), True),
        ("foo/*", "*/*", True),
        ("foo/*", headers.Matched.parse("*/*"), True),
        ("*/*", "foo/bar", True),
        ("*/*", headers.Matched.parse("foo/bar"), True),
        ("*/*", "foo/*", True),
        ("*/*", headers.Matched.parse("foo/*"), True),
        ("*/*", "*/*", True),
        ("*/*", headers.Matched.parse("*/*"), True),
    ),
)
def test_accept_matching(value, other, outcome):
    assert bool(headers.Matched.parse(value).match(other)) is outcome


@pytest.mark.parametrize("value", ("foo/bar", "foo/*", "*/*"))
def test_value_in_accept(value):
    acceptable = headers.parse_accept(value)
    assert acceptable.match("foo/bar")
    assert acceptable.match("foo/*")
    assert acceptable.match("*/*")


@pytest.mark.parametrize("value", ("foo/bar", "foo/*"))
def test_value_not_in_accept(value):
    acceptable = headers.parse_accept(value)
    assert not acceptable.match("no/match")
    assert not acceptable.match("no/*")
    assert "*/*" not in acceptable
    assert "*/bar" not in acceptable


@pytest.mark.parametrize(
    "header,expected",
    (
        (
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",  # noqa: E501
            [
                "text/html",
                "application/xhtml+xml",
                "image/avif",
                "image/webp",
                "application/xml;q=0.9",
                "*/*;q=0.8",
            ],
        ),
    ),
)
def test_browser_headers_general(header, expected):
    request = Request(b"/", {"accept": header}, "1.1", "GET", None, None)
    assert [str(item) for item in request.accept] == expected


@pytest.mark.parametrize(
    "header,expected",
    (
        (
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",  # noqa: E501
            [
                ("text/html", 1.0),
                ("application/xhtml+xml", 1.0),
                ("image/avif", 1.0),
                ("image/webp", 1.0),
                ("application/xml", 0.9),
                ("*/*", 0.8),
            ],
        ),
    ),
)
def test_browser_headers_specific(header, expected):
    mimes = [e[0] for e in expected]
    qs = [e[1] for e in expected]
    request = Request(b"/", {"accept": header}, "1.1", "GET", None, None)
    assert request.accept == mimes
    for a, m, q in zip(request.accept, mimes, qs):
        assert a == m
        assert a.mime == m
        assert a.q == q


@pytest.mark.parametrize(
    "raw",
    (
        "text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8",
        "application/xml;q=0.9, */*;q=0.8, text/html, application/xhtml+xml",
        (
            "foo/bar;q=0.9, */*;q=0.8, text/html=0.8, "
            "text/plain, application/xhtml+xml"
        ),
    ),
)
def test_accept_ordering(raw):
    """Should sort by q but also be stable."""
    accept = headers.parse_accept(raw)
    assert accept[0].type == "text"
    raw1 = ", ".join(str(a) for a in accept)
    accept = headers.parse_accept(raw1)
    raw2 = ", ".join(str(a) for a in accept)
    assert raw1 == raw2


def test_not_accept_wildcard():
    accept = headers.parse_accept("*/*, foo/*, */bar, foo/bar;q=0.1")
    assert not accept.match(
        "text/html", "foo/foo", "bar/bar", accept_wildcards=False
    )
    # Should ignore wildcards in accept but still matches them from mimes
    m = accept.match("text/plain", "*/*", accept_wildcards=False)
    assert m.mime == "*/*"
    assert m.match("*/*")
    assert m.header == "foo/bar"
    assert not accept.match(
        "text/html", "foo/foo", "bar/bar", accept_wildcards=False
    )


def test_accept_misc():
    header = (
        "foo/bar;q=0.0, */plain;param=123, text/plain, text/*, foo/bar;q=0.5"
    )
    a = headers.parse_accept(header)
    assert repr(a) == (
        "[*/plain;param=123, text/plain, text/*, "
        "foo/bar;q=0.5, foo/bar;q=0.0]"
    )  # noqa: E501
    assert str(a) == (
        "*/plain;param=123, text/plain, text/*, "
        "foo/bar;q=0.5, foo/bar;q=0.0"
    )  # noqa: E501
    # q=1 types don't match foo/bar but match the two others,
    # text/* comes first and matches */plain because it
    # comes first in the header
    m = a.match("foo/bar", "text/*", "text/plain")
    assert repr(m) == "<text/* matched */plain;param=123>"
    assert m == "text/*"
    assert m.mime == "text/*"
    assert m.header.mime == "*/plain"
    assert m.header.type == "*"
    assert m.header.subtype == "plain"
    assert m.header.q == 1.0
    assert m.header.params == dict(param="123")
    # Matches object against another Matched object (by mime and header)
    assert m == a.match("text/*")
    # Against unsupported type falls back to object id matching
    assert m != 123
    # Matches the highest q value
    m = a.match("foo/bar")
    assert repr(m) == "<foo/bar matched foo/bar;q=0.5>"
    assert m == "foo/bar"
    assert m == "foo/bar;q=0.5"
    # Matching nothing special case
    m = a.match()
    assert m == ""
    assert m.header is None
    # No header means anything
    a = headers.parse_accept(None)
    assert a == ["*/*"]
    assert a.match("foo/bar")
    # Empty header means nothing
    a = headers.parse_accept("")
    assert a == []
    assert not a.match("foo/bar")


@pytest.mark.parametrize(
    "headers,expected",
    (
        ({"foo": "bar"}, "bar"),
        ((("foo", "bar"), ("foo", "baz")), "bar,baz"),
        ({}, ""),
    ),
)
def test_field_simple_accessor(headers, expected):
    request = make_request(headers)
    assert request.headers.foo == request.headers.foo_ == expected


@pytest.mark.parametrize(
    "headers,expected",
    (
        ({"foo-bar": "bar"}, "bar"),
        ((("foo-bar", "bar"), ("foo-bar", "baz")), "bar,baz"),
    ),
)
def test_field_hyphenated_accessor(headers, expected):
    request = make_request(headers)
    assert request.headers.foo_bar == request.headers.foo_bar_ == expected


def test_bad_accessor():
    request = make_request({})
    msg = "'Header' object has no attribute '_foo'"
    with pytest.raises(AttributeError, match=msg):
        request.headers._foo


def test_multiple_fields_accessor(app: Sanic):
    @app.get("")
    async def handler(request: Request):
        return json({"field": request.headers.example_field})

    _, response = app.test_client.get(
        "/", headers=(("Example-Field", "Foo, Bar"), ("Example-Field", "Baz"))
    )
    assert response.json["field"] == "Foo, Bar,Baz"
