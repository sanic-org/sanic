import asyncio
import inspect
import os

from collections import namedtuple
from logging import ERROR, LogRecord
from mimetypes import guess_type
from random import choice
from typing import Callable, List
from urllib.parse import unquote

import pytest

from aiofiles import os as async_os
from pytest import LogCaptureFixture

from sanic import Request, Sanic
from sanic.compat import Header
from sanic.cookies import CookieJar
from sanic.response import (
    HTTPResponse,
    empty,
    file,
    file_stream,
    json,
    raw,
    stream,
    text,
)


JSON_DATA = {"ok": True}


@pytest.mark.filterwarnings("ignore:Types other than str will be")
def test_response_body_not_a_string(app):
    """Test when a response body sent from the application is not a string"""
    random_num = choice(range(1000))

    @app.route("/hello")
    async def hello_route(request: Request):
        return text(random_num)

    request, response = app.test_client.get("/hello")
    assert response.status == 500
    assert b"Internal Server Error" in response.body


async def sample_streaming_fn(response):
    await response.write("foo,")
    await asyncio.sleep(0.001)
    await response.write("bar")


def test_method_not_allowed():
    app = Sanic("app")

    @app.get("/")
    async def test_get(request: Request):
        return response.json({"hello": "world"})

    request, response = app.test_client.head("/")
    assert set(response.headers["Allow"].split(", ")) == {
        "GET",
    }

    request, response = app.test_client.post("/")
    assert set(response.headers["Allow"].split(", ")) == {
        "GET",
    }

    app.router.reset()

    @app.post("/")
    async def test_post(request: Request):
        return response.json({"hello": "world"})

    request, response = app.test_client.head("/")
    assert response.status == 405
    assert set(response.headers["Allow"].split(", ")) == {
        "GET",
        "POST",
    }
    assert response.headers["Content-Length"] == "0"

    request, response = app.test_client.patch("/")
    assert response.status == 405
    assert set(response.headers["Allow"].split(", ")) == {
        "GET",
        "POST",
    }
    assert response.headers["Content-Length"] == "0"


def test_response_header(app):
    @app.get("/")
    async def test(request: Request):
        return json({"ok": True}, headers={"CONTENT-TYPE": "application/json"})

    request, response = app.test_client.get("/")
    assert dict(response.headers) == {
        "connection": "keep-alive",
        "content-length": "11",
        "content-type": "application/json",
    }


def test_response_content_length(app):
    @app.get("/response_with_space")
    async def response_with_space(request: Request):
        return json(
            {"message": "Data", "details": "Some Details"},
            headers={"CONTENT-TYPE": "application/json"},
        )

    @app.get("/response_without_space")
    async def response_without_space(request: Request):
        return json(
            {"message": "Data", "details": "Some Details"},
            headers={"CONTENT-TYPE": "application/json"},
        )

    _, response = app.test_client.get("/response_with_space")
    content_length_for_response_with_space = response.headers.get(
        "Content-Length"
    )

    _, response = app.test_client.get("/response_without_space")
    content_length_for_response_without_space = response.headers.get(
        "Content-Length"
    )

    assert (
        content_length_for_response_with_space
        == content_length_for_response_without_space
    )

    assert content_length_for_response_with_space == "43"


def test_response_content_length_with_different_data_types(app):
    @app.get("/")
    async def get_data_with_different_types(request: Request):
        # Indentation issues in the Response is intentional. Please do not fix
        return json(
            {"bool": True, "none": None, "string": "string", "number": -1},
            headers={"CONTENT-TYPE": "application/json"},
        )

    _, response = app.test_client.get("/")
    assert response.headers.get("Content-Length") == "55"


@pytest.fixture
def json_app(app):
    @app.route("/")
    async def test(request: Request):
        return json(JSON_DATA)

    @app.get("/no-content")
    async def no_content_handler(request: Request):
        return json(JSON_DATA, status=204)

    @app.get("/no-content/unmodified")
    async def no_content_unmodified_handler(request: Request):
        return json(None, status=304)

    @app.get("/unmodified")
    async def unmodified_handler(request: Request):
        return json(JSON_DATA, status=304)

    @app.delete("/")
    async def delete_handler(request: Request):
        return json(None, status=204)

    return app


def test_json_response(json_app):
    from sanic.response import json_dumps

    request, response = json_app.test_client.get("/")
    assert response.status == 200
    assert response.text == json_dumps(JSON_DATA)
    assert response.json == JSON_DATA


def test_no_content(json_app):
    request, response = json_app.test_client.get("/no-content")
    assert response.status == 204
    assert response.text == ""
    assert "Content-Length" not in response.headers

    request, response = json_app.test_client.get("/no-content/unmodified")
    assert response.status == 304
    assert response.text == ""
    assert "Content-Length" not in response.headers
    assert "Content-Type" not in response.headers

    request, response = json_app.test_client.get("/unmodified")
    assert response.status == 304
    assert response.text == ""
    assert "Content-Length" not in response.headers
    assert "Content-Type" not in response.headers

    request, response = json_app.test_client.delete("/")
    assert response.status == 204
    assert response.text == ""
    assert "Content-Length" not in response.headers


@pytest.fixture
def streaming_app(app):
    @app.route("/")
    async def test(request: Request):
        return stream(
            sample_streaming_fn,
            content_type="text/csv",
        )

    return app


@pytest.fixture
def non_chunked_streaming_app(app):
    @app.route("/")
    async def test(request: Request):
        return stream(
            sample_streaming_fn,
            headers={"Content-Length": "7"},
            content_type="text/csv",
        )

    return app


def test_chunked_streaming_adds_correct_headers(streaming_app):
    request, response = streaming_app.test_client.get("/")
    assert response.headers["Transfer-Encoding"] == "chunked"
    assert response.headers["Content-Type"] == "text/csv"
    # Content-Length is not allowed by HTTP/1.1 specification
    # when "Transfer-Encoding: chunked" is used
    assert "Content-Length" not in response.headers


def test_chunked_streaming_returns_correct_content(streaming_app):
    request, response = streaming_app.test_client.get("/")
    assert response.text == "foo,bar"


@pytest.mark.asyncio
async def test_chunked_streaming_returns_correct_content_asgi(streaming_app):
    request, response = await streaming_app.asgi_client.get("/")
    assert response.body == b"foo,bar"


def test_non_chunked_streaming_adds_correct_headers(non_chunked_streaming_app):
    request, response = non_chunked_streaming_app.test_client.get("/")

    assert "Transfer-Encoding" not in response.headers
    assert response.headers["Content-Type"] == "text/csv"
    assert response.headers["Content-Length"] == "7"


@pytest.mark.asyncio
async def test_non_chunked_streaming_adds_correct_headers_asgi(
    non_chunked_streaming_app,
):
    request, response = await non_chunked_streaming_app.asgi_client.get("/")
    assert "Transfer-Encoding" not in response.headers
    assert response.headers["Content-Type"] == "text/csv"
    assert response.headers["Content-Length"] == "7"


def test_non_chunked_streaming_returns_correct_content(
    non_chunked_streaming_app,
):
    request, response = non_chunked_streaming_app.test_client.get("/")
    assert response.text == "foo,bar"


def test_stream_response_with_cookies_legacy(app):
    @app.route("/")
    async def test(request: Request):
        response = stream(sample_streaming_fn, content_type="text/csv")
        response.cookies["test"] = "modified"
        response.cookies["test"] = "pass"
        return response

    request, response = app.test_client.get("/")
    assert response.cookies["test"] == "pass"


def test_stream_response_with_cookies(app):
    @app.route("/")
    async def test(request: Request):
        headers = Header()
        cookies = CookieJar(headers)
        cookies["test"] = "modified"
        cookies["test"] = "pass"
        response = await request.respond(
            content_type="text/csv", headers=headers
        )

        await response.send("foo,")
        await asyncio.sleep(0.001)
        await response.send("bar")

    request, response = app.test_client.get("/")
    assert response.cookies["test"] == "pass"


def test_stream_response_without_cookies(app):
    @app.route("/")
    async def test(request: Request):
        return stream(sample_streaming_fn, content_type="text/csv")

    request, response = app.test_client.get("/")
    assert response.cookies == {}


@pytest.fixture
def static_file_directory():
    """The static directory to serve"""
    current_file = inspect.getfile(inspect.currentframe())
    current_directory = os.path.dirname(os.path.abspath(current_file))
    static_directory = os.path.join(current_directory, "static")
    return static_directory


def get_file_content(static_file_directory, file_name):
    """The content of the static file to check"""
    with open(os.path.join(static_file_directory, file_name), "rb") as file:
        return file.read()


@pytest.mark.parametrize(
    "file_name", ["test.file", "decode me.txt", "python.png"]
)
@pytest.mark.parametrize("status", [200, 401])
def test_file_response(app: Sanic, file_name, static_file_directory, status):
    @app.route("/files/<filename>", methods=["GET"])
    def file_route(request, filename):
        file_path = os.path.join(static_file_directory, filename)
        file_path = os.path.abspath(unquote(file_path))
        return file(
            file_path,
            status=status,
            mime_type=guess_type(file_path)[0] or "text/plain",
        )

    request, response = app.test_client.get(f"/files/{file_name}")
    assert response.status == status
    assert response.body == get_file_content(static_file_directory, file_name)
    assert "Content-Disposition" not in response.headers


@pytest.mark.parametrize(
    "source,dest",
    [
        ("test.file", "my_file.txt"),
        ("decode me.txt", "readme.md"),
        ("python.png", "logo.png"),
    ],
)
def test_file_response_custom_filename(
    app: Sanic, source, dest, static_file_directory
):
    @app.route("/files/<filename>", methods=["GET"])
    def file_route(request, filename):
        file_path = os.path.join(static_file_directory, filename)
        file_path = os.path.abspath(unquote(file_path))
        return file(file_path, filename=dest)

    request, response = app.test_client.get(f"/files/{source}")
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, source)
    assert (
        response.headers["Content-Disposition"]
        == f'attachment; filename="{dest}"'
    )


@pytest.mark.parametrize("file_name", ["test.file", "decode me.txt"])
def test_file_head_response(app: Sanic, file_name, static_file_directory):
    @app.route("/files/<filename>", methods=["GET", "HEAD"])
    async def file_route(request, filename):
        file_path = os.path.join(static_file_directory, filename)
        file_path = os.path.abspath(unquote(file_path))
        stats = await async_os.stat(file_path)
        headers = {}
        headers["Accept-Ranges"] = "bytes"
        headers["Content-Length"] = str(stats.st_size)
        if request.method == "HEAD":
            return HTTPResponse(
                headers=headers,
                content_type=guess_type(file_path)[0] or "text/plain",
            )
        else:
            return file(
                file_path,
                headers=headers,
                mime_type=guess_type(file_path)[0] or "text/plain",
            )

    request, response = app.test_client.head(f"/files/{file_name}")
    assert response.status == 200
    assert "Accept-Ranges" in response.headers
    assert "Content-Length" in response.headers
    assert int(response.headers["Content-Length"]) == len(
        get_file_content(static_file_directory, file_name)
    )


@pytest.mark.parametrize(
    "file_name", ["test.file", "decode me.txt", "python.png"]
)
def test_file_stream_response(app: Sanic, file_name, static_file_directory):
    @app.route("/files/<filename>", methods=["GET"])
    def file_route(request, filename):
        file_path = os.path.join(static_file_directory, filename)
        file_path = os.path.abspath(unquote(file_path))
        return file_stream(
            file_path,
            chunk_size=32,
            mime_type=guess_type(file_path)[0] or "text/plain",
        )

    request, response = app.test_client.get(f"/files/{file_name}")
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, file_name)
    assert "Content-Disposition" not in response.headers


@pytest.mark.parametrize(
    "source,dest",
    [
        ("test.file", "my_file.txt"),
        ("decode me.txt", "readme.md"),
        ("python.png", "logo.png"),
    ],
)
def test_file_stream_response_custom_filename(
    app: Sanic, source, dest, static_file_directory
):
    @app.route("/files/<filename>", methods=["GET"])
    def file_route(request, filename):
        file_path = os.path.join(static_file_directory, filename)
        file_path = os.path.abspath(unquote(file_path))
        return file_stream(file_path, chunk_size=32, filename=dest)

    request, response = app.test_client.get(f"/files/{source}")
    assert response.status == 200
    assert response.body == get_file_content(static_file_directory, source)
    assert (
        response.headers["Content-Disposition"]
        == f'attachment; filename="{dest}"'
    )


@pytest.mark.parametrize("file_name", ["test.file", "decode me.txt"])
def test_file_stream_head_response(
    app: Sanic, file_name, static_file_directory
):
    @app.route("/files/<filename>", methods=["GET", "HEAD"])
    async def file_route(request, filename):
        file_path = os.path.join(static_file_directory, filename)
        file_path = os.path.abspath(unquote(file_path))
        headers = {}
        headers["Accept-Ranges"] = "bytes"
        if request.method == "HEAD":
            # Return a normal HTTPResponse, not a
            # StreamingHTTPResponse for a HEAD request
            stats = await async_os.stat(file_path)
            headers["Content-Length"] = str(stats.st_size)
            return HTTPResponse(
                headers=headers,
                content_type=guess_type(file_path)[0] or "text/plain",
            )
        else:
            return file_stream(
                file_path,
                chunk_size=32,
                headers=headers,
                mime_type=guess_type(file_path)[0] or "text/plain",
            )

    request, response = app.test_client.head(f"/files/{file_name}")
    assert response.status == 200
    # A HEAD request should never be streamed/chunked.
    if "Transfer-Encoding" in response.headers:
        assert response.headers["Transfer-Encoding"] != "chunked"
    assert "Accept-Ranges" in response.headers
    # A HEAD request should get the Content-Length too
    assert "Content-Length" in response.headers
    assert int(response.headers["Content-Length"]) == len(
        get_file_content(static_file_directory, file_name)
    )


@pytest.mark.parametrize(
    "file_name", ["test.file", "decode me.txt", "python.png"]
)
@pytest.mark.parametrize(
    "size,start,end", [(1024, 0, 1024), (4096, 1024, 8192)]
)
def test_file_stream_response_range(
    app: Sanic, file_name, static_file_directory, size, start, end
):

    Range = namedtuple("Range", ["size", "start", "end", "total"])
    total = len(get_file_content(static_file_directory, file_name))
    range = Range(size=size, start=start, end=end, total=total)

    @app.route("/files/<filename>", methods=["GET"])
    def file_route(request, filename):
        file_path = os.path.join(static_file_directory, filename)
        file_path = os.path.abspath(unquote(file_path))
        return file_stream(
            file_path,
            chunk_size=32,
            mime_type=guess_type(file_path)[0] or "text/plain",
            _range=range,
        )

    request, response = app.test_client.get(f"/files/{file_name}")
    assert response.status == 206
    assert "Content-Range" in response.headers
    assert (
        response.headers["Content-Range"]
        == f"bytes {range.start}-{range.end}/{range.total}"
    )


def test_raw_response(app):
    @app.get("/test")
    def handler(request: Request):
        return raw(b"raw_response")

    request, response = app.test_client.get("/test")
    assert response.content_type == "application/octet-stream"
    assert response.body == b"raw_response"


def test_empty_response(app):
    @app.get("/test")
    def handler(request: Request):
        return empty()

    request, response = app.test_client.get("/test")
    assert response.content_type is None
    assert response.body == b""


def test_direct_response_stream(app: Sanic):
    @app.route("/")
    async def test(request: Request):
        response = await request.respond(content_type="text/csv")
        await response.send("foo,")
        await response.send("bar")
        await response.eof()

    _, response = app.test_client.get("/")
    assert response.text == "foo,bar"
    assert response.headers["Transfer-Encoding"] == "chunked"
    assert response.headers["Content-Type"] == "text/csv"
    assert "Content-Length" not in response.headers


def test_two_respond_calls(app: Sanic):
    @app.route("/")
    async def handler(request: Request):
        response = await request.respond()
        await response.send("foo,")
        await response.send("bar")
        await response.eof()


def test_multiple_responses(
    app: Sanic,
    caplog: LogCaptureFixture,
    message_in_records: Callable[[List[LogRecord], str], bool],
):
    @app.route("/1")
    async def handler1(request: Request):
        response = await request.respond()
        await response.send("foo")
        response = await request.respond()

    @app.route("/2")
    async def handler2(request: Request):
        response = await request.respond()
        response = await request.respond()
        await response.send("foo")

    @app.get("/3")
    async def handler3(request: Request):
        response = await request.respond()
        await response.send("foo,")
        response = await request.respond()
        await response.send("bar")

    @app.get("/4")
    async def handler4(request: Request):
        response = await request.respond(headers={"one": "one"})
        return json({"foo": "bar"}, headers={"one": "two"})

    @app.get("/5")
    async def handler5(request: Request):
        response = await request.respond(headers={"one": "one"})
        await response.send("foo")
        return json({"foo": "bar"}, headers={"one": "two"})

    @app.get("/6")
    async def handler6(request: Request):
        response = await request.respond(headers={"one": "one"})
        await response.send("foo, ")
        json_response = json({"foo": "bar"}, headers={"one": "two"})
        await response.send("bar")
        return json_response

    error_msg0 = "Second respond call is not allowed."

    error_msg1 = (
        "The error response will not be sent to the client for the following "
        'exception:"Second respond call is not allowed.". A previous '
        "response has at least partially been sent."
    )

    error_msg2 = (
        "The response object returned by the route handler "
        "will not be sent to client. The request has already "
        "been responded to."
    )

    error_msg3 = (
        "Response stream was ended, no more "
        "response data is allowed to be sent."
    )

    with caplog.at_level(ERROR):
        _, response = app.test_client.get("/1")
        assert response.status == 200
        assert message_in_records(caplog.records, error_msg0)
        assert message_in_records(caplog.records, error_msg1)

    with caplog.at_level(ERROR):
        _, response = app.test_client.get("/2")
        assert response.status == 500
        assert "500 — Internal Server Error" in response.text

    with caplog.at_level(ERROR):
        _, response = app.test_client.get("/3")
        assert response.status == 200
        assert "foo," in response.text
        assert message_in_records(caplog.records, error_msg0)
        assert message_in_records(caplog.records, error_msg1)

    with caplog.at_level(ERROR):
        _, response = app.test_client.get("/4")
        print(response.json)
        assert response.status == 200
        assert "foo" not in response.text
        assert "one" in response.headers
        assert response.headers["one"] == "one"

        print(response.headers)
        assert message_in_records(caplog.records, error_msg2)

    with caplog.at_level(ERROR):
        _, response = app.test_client.get("/5")
        assert response.status == 200
        assert "foo" in response.text
        assert "one" in response.headers
        assert response.headers["one"] == "one"
        assert message_in_records(caplog.records, error_msg2)

    with caplog.at_level(ERROR):
        _, response = app.test_client.get("/6")
        assert "foo, bar" in response.text
        assert "one" in response.headers
        assert response.headers["one"] == "one"
        assert message_in_records(caplog.records, error_msg2)


def send_response_after_eof_should_fail(
    app: Sanic,
    caplog: LogCaptureFixture,
    message_in_records: Callable[[List[LogRecord], str], bool],
):
    @app.get("/")
    async def handler(request: Request):
        response = await request.respond()
        await response.send("foo, ")
        await response.eof()
        await response.send("bar")

    error_msg1 = (
        "The error response will not be sent to the client for the following "
        'exception:"Second respond call is not allowed.". A previous '
        "response has at least partially been sent."
    )

    error_msg2 = (
        "Response stream was ended, no more "
        "response data is allowed to be sent."
    )

    with caplog.at_level(ERROR):
        _, response = app.test_client.get("/")
        assert "foo, " in response.text
        assert message_in_records(caplog.records, error_msg1)
        assert message_in_records(caplog.records, error_msg2)
