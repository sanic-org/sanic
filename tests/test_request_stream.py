import asyncio

from contextlib import closing
from socket import socket

import pytest

from sanic import Sanic
from sanic.blueprints import Blueprint
from sanic.response import json, text
from sanic.server import HttpProtocol
from sanic.views import CompositionView, HTTPMethodView
from sanic.views import stream as stream_decorator


data = "abc" * 1_000_000


def test_request_stream_method_view(app):
    class SimpleView(HTTPMethodView):
        def get(self, request):
            return text("OK")

        @stream_decorator
        async def post(self, request):
            result = b""
            while True:
                body = await request.stream.read()
                if body is None:
                    break
                result += body
            return text(result.decode())

    app.add_route(SimpleView.as_view(), "/method_view")

    request, response = app.test_client.get("/method_view")
    assert response.status == 200
    assert response.text == "OK"

    request, response = app.test_client.post("/method_view", data=data)
    assert response.status == 200
    assert response.text == data


@pytest.mark.parametrize(
    "headers, expect_raise_exception",
    [
        ({"EXPECT": "100-continue"}, False),
        # The below test SHOULD work, and it does produce a 417
        # However, httpx now intercepts this and raises an exception,
        # so we will need a new method for testing this
        # ({"EXPECT": "100-continue-extra"}, True),
    ],
)
def test_request_stream_100_continue(app, headers, expect_raise_exception):
    class SimpleView(HTTPMethodView):
        @stream_decorator
        async def post(self, request):
            result = ""
            while True:
                body = await request.stream.read()
                if body is None:
                    break
                result += body.decode("utf-8")
            return text(result)

    app.add_route(SimpleView.as_view(), "/method_view")

    if not expect_raise_exception:
        request, response = app.test_client.post(
            "/method_view", data=data, headers=headers
        )
        assert response.status == 200
        assert response.text == data
    else:
        request, response = app.test_client.post(
            "/method_view", data=data, headers=headers
        )
        assert response.status == 417


def test_request_stream_app(app):
    @app.get("/get")
    async def get(request):
        return text("GET")

    @app.head("/head")
    async def head(request):
        return text("HEAD")

    @app.delete("/delete")
    async def delete(request):
        return text("DELETE")

    @app.options("/options")
    async def options(request):
        return text("OPTIONS")

    @app.post("/_post/<id>")
    async def _post(request, id):
        return text("_POST")

    @app.post("/post/<id>", stream=True)
    async def post(request, id):
        result = ""
        while True:
            body = await request.stream.read()
            if body is None:
                break
            result += body.decode("utf-8")
        return text(result)

    @app.put("/_put")
    async def _put(request):
        return text("_PUT")

    @app.put("/put", stream=True)
    async def put(request):
        result = ""
        while True:
            body = await request.stream.read()
            if body is None:
                break
            result += body.decode("utf-8")
        return text(result)

    @app.patch("/_patch")
    async def _patch(request):
        return text("_PATCH")

    @app.patch("/patch", stream=True)
    async def patch(request):
        result = ""
        while True:
            body = await request.stream.read()
            if body is None:
                break
            result += body.decode("utf-8")
        return text(result)

    request, response = app.test_client.get("/get")
    assert response.status == 200
    assert response.text == "GET"

    request, response = app.test_client.head("/head")
    assert response.status == 200
    assert response.text == ""

    request, response = app.test_client.delete("/delete")
    assert response.status == 200
    assert response.text == "DELETE"

    request, response = app.test_client.options("/options")
    assert response.status == 200
    assert response.text == "OPTIONS"

    request, response = app.test_client.post("/_post/1", data=data)
    assert response.status == 200
    assert response.text == "_POST"

    request, response = app.test_client.post("/post/1", data=data)
    assert response.status == 200
    assert response.text == data

    request, response = app.test_client.put("/_put", data=data)
    assert response.status == 200
    assert response.text == "_PUT"

    request, response = app.test_client.put("/put", data=data)
    assert response.status == 200
    assert response.text == data

    request, response = app.test_client.patch("/_patch", data=data)
    assert response.status == 200
    assert response.text == "_PATCH"

    request, response = app.test_client.patch("/patch", data=data)
    assert response.status == 200
    assert response.text == data


@pytest.mark.asyncio
async def test_request_stream_app_asgi(app):
    @app.get("/get")
    async def get(request):
        return text("GET")

    @app.head("/head")
    async def head(request):
        return text("HEAD")

    @app.delete("/delete")
    async def delete(request):
        return text("DELETE")

    @app.options("/options")
    async def options(request):
        return text("OPTIONS")

    @app.post("/_post/<id>")
    async def _post(request, id):
        return text("_POST")

    @app.post("/post/<id>", stream=True)
    async def post(request, id):
        result = ""
        while True:
            body = await request.stream.read()
            if body is None:
                break
            result += body.decode("utf-8")
        return text(result)

    @app.put("/_put")
    async def _put(request):
        return text("_PUT")

    @app.put("/put", stream=True)
    async def put(request):
        result = ""
        while True:
            body = await request.stream.read()
            if body is None:
                break
            result += body.decode("utf-8")
        return text(result)

    @app.patch("/_patch")
    async def _patch(request):
        return text("_PATCH")

    @app.patch("/patch", stream=True)
    async def patch(request):
        result = ""
        while True:
            body = await request.stream.read()
            if body is None:
                break
            result += body.decode("utf-8")
        return text(result)

    request, response = await app.asgi_client.get("/get")
    assert response.status == 200
    assert response.text == "GET"

    request, response = await app.asgi_client.head("/head")
    assert response.status == 200
    assert response.text == ""

    request, response = await app.asgi_client.delete("/delete")
    assert response.status == 200
    assert response.text == "DELETE"

    request, response = await app.asgi_client.options("/options")
    assert response.status == 200
    assert response.text == "OPTIONS"

    request, response = await app.asgi_client.post("/_post/1", data=data)
    assert response.status == 200
    assert response.text == "_POST"

    request, response = await app.asgi_client.post("/post/1", data=data)
    assert response.status == 200
    assert response.text == data

    request, response = await app.asgi_client.put("/_put", data=data)
    assert response.status == 200
    assert response.text == "_PUT"

    request, response = await app.asgi_client.put("/put", data=data)
    assert response.status == 200
    assert response.text == data

    request, response = await app.asgi_client.patch("/_patch", data=data)
    assert response.status == 200
    assert response.text == "_PATCH"

    request, response = await app.asgi_client.patch("/patch", data=data)
    assert response.status == 200
    assert response.text == data


def test_request_stream_handle_exception(app):
    """for handling exceptions properly"""

    @app.post("/post/<id>", stream=True)
    async def post(request, id):
        result = b""
        while True:
            body = await request.stream.read()
            if body is None:
                break
            result += body
        return text(result.decode())

    # 404
    request, response = app.test_client.post("/in_valid_post", data=data)
    assert response.status == 404
    assert "Requested URL /in_valid_post not found" in response.text

    # 405
    request, response = app.test_client.get("/post/random_id")
    assert response.status == 405
    assert "Method GET not allowed for URL /post/random_id" in response.text


def test_request_stream_blueprint(app):
    bp = Blueprint("test_blueprint_request_stream_blueprint")

    @app.get("/get")
    async def get(request):
        return text("GET")

    @bp.head("/head")
    async def head(request):
        return text("HEAD")

    @bp.delete("/delete")
    async def delete(request):
        return text("DELETE")

    @bp.options("/options")
    async def options(request):
        return text("OPTIONS")

    @bp.post("/_post/<id>")
    async def _post(request, id):
        return text("_POST")

    @bp.post("/post/<id>", stream=True)
    async def post(request, id):
        result = ""
        while True:
            body = await request.stream.read()
            if body is None:
                break
            result += body.decode("utf-8")
        return text(result)

    @bp.put("/_put")
    async def _put(request):
        return text("_PUT")

    @bp.put("/put", stream=True)
    async def put(request):
        result = ""
        while True:
            body = await request.stream.read()
            if body is None:
                break
            result += body.decode("utf-8")
        return text(result)

    @bp.patch("/_patch")
    async def _patch(request):
        return text("_PATCH")

    @bp.patch("/patch", stream=True)
    async def patch(request):
        result = ""
        while True:
            body = await request.stream.read()
            if body is None:
                break
            result += body.decode("utf-8")
        return text(result)

    async def post_add_route(request):
        result = ""
        while True:
            body = await request.stream.read()
            if body is None:
                break
            result += body.decode("utf-8")
        return text(result)

    bp.add_route(
        post_add_route, "/post/add_route", methods=["POST"], stream=True
    )
    app.blueprint(bp)

    request, response = app.test_client.get("/get")
    assert response.status == 200
    assert response.text == "GET"

    request, response = app.test_client.head("/head")
    assert response.status == 200
    assert response.text == ""

    request, response = app.test_client.delete("/delete")
    assert response.status == 200
    assert response.text == "DELETE"

    request, response = app.test_client.options("/options")
    assert response.status == 200
    assert response.text == "OPTIONS"

    request, response = app.test_client.post("/_post/1", data=data)
    assert response.status == 200
    assert response.text == "_POST"

    request, response = app.test_client.post("/post/1", data=data)
    assert response.status == 200
    assert response.text == data

    request, response = app.test_client.put("/_put", data=data)
    assert response.status == 200
    assert response.text == "_PUT"

    request, response = app.test_client.put("/put", data=data)
    assert response.status == 200
    assert response.text == data

    request, response = app.test_client.patch("/_patch", data=data)
    assert response.status == 200
    assert response.text == "_PATCH"

    request, response = app.test_client.patch("/patch", data=data)
    assert response.status == 200
    assert response.text == data

    request, response = app.test_client.post("/post/add_route", data=data)
    assert response.status == 200
    assert response.text == data


def test_request_stream_composition_view(app):
    def get_handler(request):
        return text("OK")

    async def post_handler(request):
        result = ""
        while True:
            body = await request.stream.read()
            if body is None:
                break
            result += body.decode("utf-8")
        return text(result)

    view = CompositionView()
    view.add(["GET"], get_handler)
    view.add(["POST"], post_handler, stream=True)
    app.add_route(view, "/composition_view")

    request, response = app.test_client.get("/composition_view")
    assert response.status == 200
    assert response.text == "OK"

    request, response = app.test_client.post("/composition_view", data=data)
    assert response.status == 200
    assert response.text == data


def test_request_stream(app):
    """test for complex application"""
    bp = Blueprint("test_blueprint_request_stream")

    class SimpleView(HTTPMethodView):
        def get(self, request):
            return text("OK")

        @stream_decorator
        async def post(self, request):
            result = ""
            while True:
                body = await request.stream.read()
                if body is None:
                    break
                result += body.decode("utf-8")
            return text(result)

    @app.post("/stream", stream=True)
    async def handler(request):
        result = ""
        while True:
            body = await request.stream.read()
            if body is None:
                break
            result += body.decode("utf-8")
        return text(result)

    @app.get("/get")
    async def get(request):
        return text("OK")

    @bp.post("/bp_stream", stream=True)
    async def bp_stream(request):
        result = ""
        while True:
            body = await request.stream.read()
            if body is None:
                break
            result += body.decode("utf-8")
        return text(result)

    @bp.get("/bp_get")
    async def bp_get(request):
        return text("OK")

    def get_handler(request):
        return text("OK")

    async def post_handler(request):
        result = ""
        while True:
            body = await request.stream.read()
            if body is None:
                break
            result += body.decode("utf-8")
        return text(result)

    app.add_route(SimpleView.as_view(), "/method_view")

    view = CompositionView()
    view.add(["GET"], get_handler)
    view.add(["POST"], post_handler, stream=True)

    app.blueprint(bp)

    app.add_route(view, "/composition_view")

    request, response = app.test_client.get("/method_view")
    assert response.status == 200
    assert response.text == "OK"

    request, response = app.test_client.post("/method_view", data=data)
    assert response.status == 200
    assert response.text == data

    request, response = app.test_client.get("/composition_view")
    assert response.status == 200
    assert response.text == "OK"

    request, response = app.test_client.post("/composition_view", data=data)
    assert response.status == 200
    assert response.text == data

    request, response = app.test_client.get("/get")
    assert response.status == 200
    assert response.text == "OK"

    request, response = app.test_client.post("/stream", data=data)
    assert response.status == 200
    assert response.text == data

    request, response = app.test_client.get("/bp_get")
    assert response.status == 200
    assert response.text == "OK"

    request, response = app.test_client.post("/bp_stream", data=data)
    assert response.status == 200
    assert response.text == data


def test_streaming_new_api(app):
    @app.post("/non-stream")
    async def handler1(request):
        assert request.body == b"x"
        await request.receive_body()  # This should do nothing
        assert request.body == b"x"
        return text("OK")

    @app.post("/1", stream=True)
    async def handler2(request):
        assert request.stream
        assert not request.body
        await request.receive_body()
        return text(request.body.decode().upper())

    @app.post("/2", stream=True)
    async def handler(request):
        ret = []
        async for data in request.stream:
            # We should have no b"" or None, just proper chunks
            assert data
            assert isinstance(data, bytes)
            ret.append(data.decode("ASCII"))
        return json(ret)

    request, response = app.test_client.post("/non-stream", data="x")
    assert response.status == 200

    request, response = app.test_client.post("/1", data="TEST data")
    assert request.body == b"TEST data"
    assert response.status == 200
    assert response.text == "TEST DATA"

    request, response = app.test_client.post("/2", data=data)
    assert response.status == 200
    res = response.json
    assert isinstance(res, list)
    assert "".join(res) == data


def test_streaming_echo():
    """2-way streaming chat between server and client."""
    app = Sanic(name=__name__)

    @app.post("/echo", stream=True)
    async def handler(request):
        res = await request.respond(content_type="text/plain; charset=utf-8")
        # Send headers
        await res.send(end_stream=False)
        # Echo back data (case swapped)
        async for data in request.stream:
            await res.send(data.swapcase())
        # Add EOF marker after successful operation
        await res.send(b"-", end_stream=True)

    @app.listener("after_server_start")
    async def client_task(app, loop):
        try:
            reader, writer = await asyncio.open_connection(*addr)
            await client(app, reader, writer)
        finally:
            writer.close()
            app.stop()

    async def client(app, reader, writer):
        # Unfortunately httpx does not support 2-way streaming, so do it by hand.
        host = f"host: {addr[0]}:{addr[1]}\r\n".encode()
        writer.write(
            b"POST /echo HTTP/1.1\r\n" + host + b"content-length: 2\r\n"
            b"content-type: text/plain; charset=utf-8\r\n"
            b"\r\n"
        )
        # Read response
        res = b""
        while not b"\r\n\r\n" in res:
            res += await reader.read(4096)
        assert res.startswith(b"HTTP/1.1 200 OK\r\n")
        assert res.endswith(b"\r\n\r\n")
        buffer = b""

        async def read_chunk():
            nonlocal buffer
            while not b"\r\n" in buffer:
                data = await reader.read(4096)
                assert data
                buffer += data
            size, buffer = buffer.split(b"\r\n", 1)
            size = int(size, 16)
            if size == 0:
                return None
            while len(buffer) < size + 2:
                data = await reader.read(4096)
                assert data
                buffer += data
            assert buffer[size : size + 2] == b"\r\n"
            ret, buffer = buffer[:size], buffer[size + 2 :]
            return ret

        # Chat with server
        writer.write(b"a")
        res = await read_chunk()
        assert res == b"A"

        writer.write(b"b")
        res = await read_chunk()
        assert res == b"B"

        res = await read_chunk()
        assert res == b"-"

        res = await read_chunk()
        assert res == None

    # Use random port for tests
    with closing(socket()) as sock:
        sock.bind(("127.0.0.1", 0))
        addr = sock.getsockname()
        app.run(sock=sock, access_log=False)
