import pytest

from sanic.headers import format_http1_response
from sanic.response import text
from sanic.response.convenience import file


def encoded_header_values(response):
    return list(response.processed_headers)


def wire(response):
    return format_http1_response(response.status, response.processed_headers)


def test_response_header_value_strips_crlf():
    response = text("ok")
    response.headers["X-Test"] = "ok\r\nX-Injected: hdr"

    for _, value in encoded_header_values(response):
        assert b"\r" not in value and b"\n" not in value

    assert b"\r\nX-Injected:" not in wire(response)


def test_cookie_attribute_strips_crlf():
    response = text("ok")
    response.add_cookie("demo", "1", path="/test\r\nSet-Cookie: attacker=1")

    for _, value in encoded_header_values(response):
        assert b"\r" not in value and b"\n" not in value

    assert b"\r\nSet-Cookie: attacker=1" not in wire(response)


@pytest.mark.asyncio
async def test_file_filename_strips_crlf():
    response = await file(__file__, filename='name.txt"\r\nInjected: yes')

    for _, value in encoded_header_values(response):
        assert b"\r" not in value and b"\n" not in value

    assert b"\r\nInjected: yes" not in wire(response)


def test_response_header_name_strips_crlf():
    response = text("ok")
    response.headers["X-Foo\r\nX-Injected: evil"] = "bar"

    for name, _ in encoded_header_values(response):
        assert b"\r" not in name and b"\n" not in name

    assert b"\r\nX-Injected:" not in wire(response)


def test_content_type_strips_crlf():
    response = text("ok", content_type="text/plain\r\nX-Injected: evil")

    for _, value in encoded_header_values(response):
        assert b"\r" not in value and b"\n" not in value

    assert b"\r\nX-Injected:" not in wire(response)


def test_header_value_strips_nul():
    response = text("ok")
    response.headers["X-Test"] = "a\x00b"

    for _, value in encoded_header_values(response):
        assert b"\x00" not in value
