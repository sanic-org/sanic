import pytest

from sanic.blueprints import Blueprint
from sanic.exceptions import HeaderExpectationFailed
from sanic.response import json, stream, text
from sanic.views import CompositionView, HTTPMethodView
from sanic.views import stream as stream_decorator


data = "abc" * 10000000


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
        ({"EXPECT": "100-continue-extra"}, True),
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
            "/method_view", data=data, headers={"EXPECT": "100-continue"}
        )
        assert response.status == 200
        assert response.text == data
    else:
        with pytest.raises(ValueError) as e:
            app.test_client.post(
                "/method_view",
                data=data,
                headers={"EXPECT": "100-continue-extra"},
            )
            assert "Unknown Expect: 100-continue-extra" in str(e)


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
    @app.post("/1", stream=True)
    async def handler(request):
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
            ret.append(data)
        return json(ret)

    request, response = app.test_client.post("/1", data="TEST data")
    assert request.body == b"TEST data"
    assert response.status == 200
    assert response.text == "TEST DATA"

    request, response = app.test_client.post("/2", data=data)
    assert response.status == 200
    res = response.json
    assert isinstance(res, list)
    assert len(res) > 1
    assert "".join(res) == data
