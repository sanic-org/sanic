import asyncio
import re

import pytest

from sanic_routing.exceptions import (
    InvalidUsage,
    ParameterNameConflicts,
    RouteExists,
)
from sanic_testing.testing import SanicTestClient

from sanic import Blueprint, Sanic
from sanic.constants import HTTP_METHODS
from sanic.exceptions import NotFound, SanicException
from sanic.request import Request
from sanic.response import empty, json, text


@pytest.mark.parametrize(
    "path,headers,expected",
    (
        # app base
        (b"/", {}, 200),
        (b"/", {"host": "maybe.com"}, 200),
        (b"/host", {"host": "matching.com"}, 200),
        (b"/host", {"host": "wrong.com"}, 404),
        # app strict_slashes default
        (b"/without", {}, 200),
        (b"/without/", {}, 200),
        (b"/with", {}, 200),
        (b"/with/", {}, 200),
        # app strict_slashes off - expressly
        (b"/expwithout", {}, 200),
        (b"/expwithout/", {}, 200),
        (b"/expwith", {}, 200),
        (b"/expwith/", {}, 200),
        # app strict_slashes on
        (b"/without/strict", {}, 200),
        (b"/without/strict/", {}, 404),
        (b"/with/strict", {}, 404),
        (b"/with/strict/", {}, 200),
        # bp1 base
        (b"/bp1", {}, 200),
        (b"/bp1", {"host": "maybe.com"}, 200),
        (b"/bp1/host", {"host": "matching.com"}, 200),  # BROKEN ON MASTER
        (b"/bp1/host", {"host": "wrong.com"}, 404),
        # bp1 strict_slashes default
        (b"/bp1/without", {}, 200),
        (b"/bp1/without/", {}, 200),
        (b"/bp1/with", {}, 200),
        (b"/bp1/with/", {}, 200),
        # bp1 strict_slashes off - expressly
        (b"/bp1/expwithout", {}, 200),
        (b"/bp1/expwithout/", {}, 200),
        (b"/bp1/expwith", {}, 200),
        (b"/bp1/expwith/", {}, 200),
        # bp1 strict_slashes on
        (b"/bp1/without/strict", {}, 200),
        (b"/bp1/without/strict/", {}, 404),
        (b"/bp1/with/strict", {}, 404),
        (b"/bp1/with/strict/", {}, 200),
        # bp2 base
        (b"/bp2/", {}, 200),
        (b"/bp2/", {"host": "maybe.com"}, 200),
        (b"/bp2/host", {"host": "matching.com"}, 200),  # BROKEN ON MASTER
        (b"/bp2/host", {"host": "wrong.com"}, 404),
        # bp2 strict_slashes default
        (b"/bp2/without", {}, 200),
        (b"/bp2/without/", {}, 404),
        (b"/bp2/with", {}, 404),
        (b"/bp2/with/", {}, 200),
        # # bp2 strict_slashes off - expressly
        (b"/bp2/expwithout", {}, 200),
        (b"/bp2/expwithout/", {}, 200),
        (b"/bp2/expwith", {}, 200),
        (b"/bp2/expwith/", {}, 200),
        # # bp2 strict_slashes on
        (b"/bp2/without/strict", {}, 200),
        (b"/bp2/without/strict/", {}, 404),
        (b"/bp2/with/strict", {}, 404),
        (b"/bp2/with/strict/", {}, 200),
        # bp3 base
        (b"/bp3", {}, 200),
        (b"/bp3", {"host": "maybe.com"}, 200),
        (b"/bp3/host", {"host": "matching.com"}, 200),  # BROKEN ON MASTER
        (b"/bp3/host", {"host": "wrong.com"}, 404),
        # bp3 strict_slashes default
        (b"/bp3/without", {}, 200),
        (b"/bp3/without/", {}, 200),
        (b"/bp3/with", {}, 200),
        (b"/bp3/with/", {}, 200),
        # bp3 strict_slashes off - expressly
        (b"/bp3/expwithout", {}, 200),
        (b"/bp3/expwithout/", {}, 200),
        (b"/bp3/expwith", {}, 200),
        (b"/bp3/expwith/", {}, 200),
        # bp3 strict_slashes on
        (b"/bp3/without/strict", {}, 200),
        (b"/bp3/without/strict/", {}, 404),
        (b"/bp3/with/strict", {}, 404),
        (b"/bp3/with/strict/", {}, 200),
        # bp4 base
        (b"/bp4", {}, 404),
        (b"/bp4", {"host": "maybe.com"}, 200),
        (b"/bp4/host", {"host": "matching.com"}, 200),  # BROKEN ON MASTER
        (b"/bp4/host", {"host": "wrong.com"}, 404),
        # bp4 strict_slashes default
        (b"/bp4/without", {}, 404),
        (b"/bp4/without/", {}, 404),
        (b"/bp4/with", {}, 404),
        (b"/bp4/with/", {}, 404),
        # bp4 strict_slashes off - expressly
        (b"/bp4/expwithout", {}, 404),
        (b"/bp4/expwithout/", {}, 404),
        (b"/bp4/expwith", {}, 404),
        (b"/bp4/expwith/", {}, 404),
        # bp4 strict_slashes on
        (b"/bp4/without/strict", {}, 404),
        (b"/bp4/without/strict/", {}, 404),
        (b"/bp4/with/strict", {}, 404),
        (b"/bp4/with/strict/", {}, 404),
    ),
)
def test_matching(path, headers, expected):
    app = Sanic("dev")
    bp1 = Blueprint("bp1", url_prefix="/bp1")
    bp2 = Blueprint("bp2", url_prefix="/bp2", strict_slashes=True)
    bp3 = Blueprint("bp3", url_prefix="/bp3", strict_slashes=False)
    bp4 = Blueprint("bp4", url_prefix="/bp4", host="maybe.com")

    def handler(request):
        return text("Hello!")

    defs = (
        ("/", None, None),
        ("/host", None, "matching.com"),
        ("/without", None, None),
        ("/with/", None, None),
        ("/expwithout", False, None),
        ("/expwith/", False, None),
        ("/without/strict", True, None),
        ("/with/strict/", True, None),
    )
    for uri, strict_slashes, host in defs:
        params = {"uri": uri}
        if strict_slashes is not None:
            params["strict_slashes"] = strict_slashes
        if host is not None:
            params["host"] = host
        app.route(**params)(handler)
        bp1.route(**params)(handler)
        bp2.route(**params)(handler)
        bp3.route(**params)(handler)
        bp4.route(**params)(handler)

    app.blueprint(bp1)
    app.blueprint(bp2)
    app.blueprint(bp3)
    app.blueprint(bp4)

    app.router.finalize()

    request = Request(path, headers, None, "GET", None, app)

    try:
        app.router.get(
            request.path, request.method, request.headers.get("host")
        )
    except NotFound:
        response = 404
    except Exception:
        response = 500
    else:
        response = 200

    assert response == expected


# # ------------------------------------------------------------ #
# #  UTF-8
# # ------------------------------------------------------------ #


@pytest.mark.parametrize("method", HTTP_METHODS)
def test_versioned_routes_get(app, method):
    method = method.lower()

    func = getattr(app, method)
    if callable(func):

        @func(f"/{method}", version=1)
        def handler(request):
            return text("OK")

    else:
        raise Exception(f"Method: {method} is not callable")

    client_method = getattr(app.test_client, method)

    request, response = client_method(f"/v1/{method}")
    assert response.status == 200


def test_shorthand_routes_get(app):
    @app.get("/get")
    def handler(request):
        return text("OK")

    request, response = app.test_client.get("/get")
    assert response.text == "OK"

    request, response = app.test_client.post("/get")
    assert response.status == 405


def test_shorthand_routes_multiple(app):
    @app.get("/get")
    def get_handler(request):
        return text("OK")

    @app.options("/get")
    def options_handler(request):
        return text("")

    request, response = app.test_client.get("/get/")
    assert response.status == 200
    assert response.text == "OK"

    request, response = app.test_client.options("/get/")
    assert response.status == 200


def test_route_strict_slash(app):
    @app.get("/get", strict_slashes=True)
    def handler1(request):
        return text("OK")

    @app.post("/post/", strict_slashes=True)
    def handler2(request):
        return text("OK")

    request, response = app.test_client.get("/get")
    assert response.text == "OK"

    request, response = app.test_client.get("/get/")
    assert response.status == 404

    request, response = app.test_client.post("/post/")
    assert response.text == "OK"

    request, response = app.test_client.post("/post")
    assert response.status == 404


def test_route_invalid_parameter_syntax(app):
    with pytest.raises(InvalidUsage):

        @app.get("/get/<:str>", strict_slashes=True)
        def handler(request):
            return text("OK")

        request, response = app.test_client.get("/get")


def test_route_strict_slash_default_value():
    app = Sanic("test_route_strict_slash", strict_slashes=True)

    @app.get("/get")
    def handler(request):
        return text("OK")

    request, response = app.test_client.get("/get/")
    assert response.status == 404


def test_route_strict_slash_without_passing_default_value(app):
    @app.get("/get")
    def handler(request):
        return text("OK")

    request, response = app.test_client.get("/get/")
    assert response.text == "OK"


def test_route_strict_slash_default_value_can_be_overwritten():
    app = Sanic("test_route_strict_slash", strict_slashes=True)

    @app.get("/get", strict_slashes=False)
    def handler(request):
        return text("OK")

    request, response = app.test_client.get("/get/")
    assert response.text == "OK"


def test_route_slashes_overload(app):
    @app.get("/hello/")
    def handler_get(request):
        return text("OK")

    @app.post("/hello/")
    def handler_post(request):
        return text("OK")

    request, response = app.test_client.get("/hello")
    assert response.text == "OK"

    request, response = app.test_client.get("/hello/")
    assert response.text == "OK"

    request, response = app.test_client.post("/hello")
    assert response.text == "OK"

    request, response = app.test_client.post("/hello/")
    assert response.text == "OK"


def test_route_optional_slash(app):
    @app.get("/get")
    def handler(request):
        return text("OK")

    request, response = app.test_client.get("/get")
    assert response.text == "OK"

    request, response = app.test_client.get("/get/")
    assert response.text == "OK"


def test_route_strict_slashes_set_to_false_and_host_is_a_list(app):
    # Part of regression test for issue #1120
    test_client = SanicTestClient(app, port=42101)
    site1 = f"127.0.0.1:{test_client.port}"

    # before fix, this raises a RouteExists error
    @app.get("/get", host=[site1, "site2.com"], strict_slashes=False)
    def get_handler(request):
        return text("OK")

    request, response = test_client.get("http://" + site1 + "/get")
    assert response.text == "OK"

    app.router.finalized = False

    @app.post("/post", host=[site1, "site2.com"], strict_slashes=False)
    def post_handler(request):
        return text("OK")

    request, response = test_client.post("http://" + site1 + "/post")
    assert response.text == "OK"

    app.router.finalized = False

    @app.put("/put", host=[site1, "site2.com"], strict_slashes=False)
    def put_handler(request):
        return text("OK")

    request, response = test_client.put("http://" + site1 + "/put")
    assert response.text == "OK"

    app.router.finalized = False

    @app.delete("/delete", host=[site1, "site2.com"], strict_slashes=False)
    def delete_handler(request):
        return text("OK")

    request, response = test_client.delete("http://" + site1 + "/delete")
    assert response.text == "OK"


def test_shorthand_routes_post(app):
    @app.post("/post")
    def handler(request):
        return text("OK")

    request, response = app.test_client.post("/post")
    assert response.text == "OK"

    request, response = app.test_client.get("/post")
    assert response.status == 405


def test_shorthand_routes_put(app):
    @app.put("/put")
    def handler(request):
        return text("OK")

    request, response = app.test_client.put("/put")
    assert response.text == "OK"

    request, response = app.test_client.get("/put")
    assert response.status == 405


def test_shorthand_routes_delete(app):
    @app.delete("/delete")
    def handler(request):
        return text("OK")

    request, response = app.test_client.delete("/delete")
    assert response.text == "OK"

    request, response = app.test_client.get("/delete")
    assert response.status == 405


def test_shorthand_routes_patch(app):
    @app.patch("/patch")
    def handler(request):
        return text("OK")

    request, response = app.test_client.patch("/patch")
    assert response.text == "OK"

    request, response = app.test_client.get("/patch")
    assert response.status == 405


def test_shorthand_routes_head(app):
    @app.head("/head")
    def handler(request):
        return text("OK")

    request, response = app.test_client.head("/head")
    assert response.status == 200

    request, response = app.test_client.get("/head")
    assert response.status == 405


def test_shorthand_routes_options(app):
    @app.options("/options")
    def handler(request):
        return text("OK")

    request, response = app.test_client.options("/options")
    assert response.status == 200

    request, response = app.test_client.get("/options")
    assert response.status == 405


def test_static_routes(app):
    @app.route("/test")
    async def handler1(request):
        return text("OK1")

    @app.route("/pizazz")
    async def handler2(request):
        return text("OK2")

    request, response = app.test_client.get("/test")
    assert response.text == "OK1"

    request, response = app.test_client.get("/pizazz")
    assert response.text == "OK2"


def test_dynamic_route(app):
    results = []

    @app.route("/folder/<name>")
    async def handler(request, name):
        results.append(name)
        return text("OK")

    app.router.finalize(False)

    request, response = app.test_client.get("/folder/test123")

    assert response.text == "OK"
    assert results[0] == "test123"


def test_dynamic_route_string(app):
    results = []

    @app.route("/folder/<name:str>")
    async def handler(request, name):
        results.append(name)
        return text("OK")

    request, response = app.test_client.get("/folder/test123")

    assert response.text == "OK"
    assert results[0] == "test123"

    request, response = app.test_client.get("/folder/favicon.ico")

    assert response.text == "OK"
    assert results[1] == "favicon.ico"


def test_dynamic_route_int(app):
    results = []

    @app.route("/folder/<folder_id:int>")
    async def handler(request, folder_id):
        results.append(folder_id)
        return text("OK")

    request, response = app.test_client.get("/folder/12345")
    assert response.text == "OK"
    assert type(results[0]) is int

    request, response = app.test_client.get("/folder/asdf")
    assert response.status == 404


def test_dynamic_route_number(app):
    results = []

    @app.route("/weight/<weight:float>")
    async def handler(request, weight):
        results.append(weight)
        return text("OK")

    request, response = app.test_client.get("/weight/12345")
    assert response.text == "OK"
    assert type(results[0]) is float

    request, response = app.test_client.get("/weight/1234.56")
    assert response.status == 200

    request, response = app.test_client.get("/weight/.12")
    assert response.status == 200

    request, response = app.test_client.get("/weight/12.")
    assert response.status == 200

    request, response = app.test_client.get("/weight/1234-56")
    assert response.status == 404

    request, response = app.test_client.get("/weight/12.34.56")
    assert response.status == 404


def test_dynamic_route_regex(app):
    @app.route("/folder/<folder_id:[A-Za-z0-9]{0,4}>")
    async def handler(request, folder_id):
        return text("OK")

    request, response = app.test_client.get("/folder/test")
    assert response.status == 200

    request, response = app.test_client.get("/folder/test1")
    assert response.status == 404

    request, response = app.test_client.get("/folder/test-123")
    assert response.status == 404

    request, response = app.test_client.get("/folder/")
    assert response.status == 200


def test_dynamic_route_uuid(app):
    import uuid

    results = []

    @app.route("/quirky/<unique_id:uuid>")
    async def handler(request, unique_id):
        results.append(unique_id)
        return text("OK")

    url = "/quirky/123e4567-e89b-12d3-a456-426655440000"
    request, response = app.test_client.get(url)
    assert response.text == "OK"
    assert type(results[0]) is uuid.UUID

    generated_uuid = uuid.uuid4()
    request, response = app.test_client.get(f"/quirky/{generated_uuid}")
    assert response.status == 200

    request, response = app.test_client.get("/quirky/non-existing")
    assert response.status == 404


def test_dynamic_route_path(app):
    @app.route("/<path:path>/info")
    async def handler(request, path):
        return text("OK")

    app.router.finalize()

    request, response = app.test_client.get("/path/1/info")
    assert response.status == 200

    request, response = app.test_client.get("/info")
    assert response.status == 404

    app.router.reset()

    @app.route("/<path:path>")
    async def handler1(request, path):
        return text("OK")

    request, response = app.test_client.get("/info")
    assert response.status == 200

    request, response = app.test_client.get("/whatever/you/set")
    assert response.status == 200


def test_dynamic_route_unhashable(app):
    @app.route("/folder/<unhashable:[A-Za-z0-9/]+>/end/")
    async def handler(request, unhashable):
        return text("OK")

    request, response = app.test_client.get("/folder/test/asdf/end/")
    assert response.status == 200

    request, response = app.test_client.get("/folder/test///////end/")
    assert response.status == 200

    request, response = app.test_client.get("/folder/test/end/")
    assert response.status == 200

    request, response = app.test_client.get("/folder/test/nope/")
    assert response.status == 404


@pytest.mark.parametrize("url", ["/ws", "ws"])
def test_websocket_route(app, url):
    ev = asyncio.Event()

    @app.websocket(url)
    async def handler(request, ws):
        assert request.scheme == "ws"
        assert ws.subprotocol is None
        ev.set()

    request, response = app.test_client.websocket(url)
    assert response.opened is True
    assert ev.is_set()


def test_websocket_route_invalid_handler(app):
    with pytest.raises(ValueError) as e:

        @app.websocket("/")
        async def handler():
            ...

    assert e.match(
        r"Required parameter `request` and/or `ws` missing in the "
        r"handler\(\) route\?"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("url", ["/ws", "ws"])
async def test_websocket_route_asgi(app, url):
    @app.after_server_start
    async def setup_ev(app, _):
        app.ctx.ev = asyncio.Event()

    @app.websocket(url)
    async def handler(request, ws):
        request.app.ctx.ev.set()

    @app.get("/ev")
    async def check(request):
        return json({"set": request.app.ctx.ev.is_set()})

    _, response = await app.asgi_client.websocket(url)
    _, response = await app.asgi_client.get("/")
    assert response.json["set"]


@pytest.mark.parametrize(
    "subprotocols,expected",
    (
        (["one"], "one"),
        (["three", "one"], "one"),
        (["tree"], None),
        (None, None),
    ),
)
def test_websocket_route_with_subprotocols(app, subprotocols, expected):
    results = []

    @app.websocket("/ws", subprotocols=["zero", "one", "two", "three"])
    async def handler(request, ws):
        nonlocal results
        results = ws.subprotocol
        assert ws.subprotocol is not None

    _, response = SanicTestClient(app).websocket(
        "/ws", subprotocols=subprotocols
    )
    assert response.opened is True
    assert results == expected


@pytest.mark.parametrize("strict_slashes", [True, False, None])
def test_add_webscoket_route(app, strict_slashes):
    ev = asyncio.Event()

    async def handler(request, ws):
        assert ws.subprotocol is None
        ev.set()

    app.add_websocket_route(handler, "/ws", strict_slashes=strict_slashes)
    request, response = app.test_client.websocket("/ws")
    assert response.opened is True
    assert ev.is_set()


def test_add_webscoket_route_with_version(app):
    ev = asyncio.Event()

    async def handler(request, ws):
        assert ws.subprotocol is None
        ev.set()

    app.add_websocket_route(handler, "/ws", version=1)
    request, response = app.test_client.websocket("/v1/ws")
    assert response.opened is True
    assert ev.is_set()


def test_route_duplicate(app):

    with pytest.raises(RouteExists):

        @app.route("/test")
        async def handler1(request):
            pass

        @app.route("/test")
        async def handler2(request):
            pass

    with pytest.raises(RouteExists):

        @app.route("/test/<dynamic>/")
        async def handler3(request, dynamic):
            pass

        @app.route("/test/<dynamic>/")
        async def handler4(request, dynamic):
            pass


def test_double_stack_route(app):
    @app.route("/test/1")
    @app.route("/test/2")
    async def handler1(request):
        return text("OK")

    request, response = app.test_client.get("/test/1")
    assert response.status == 200
    request, response = app.test_client.get("/test/2")
    assert response.status == 200


@pytest.mark.asyncio
async def test_websocket_route_asgi(app):
    ev = asyncio.Event()

    @app.websocket("/test/1")
    @app.websocket("/test/2")
    async def handler(request, ws):
        ev.set()

    request, response = await app.asgi_client.websocket("/test/1")
    first_set = ev.is_set()
    ev.clear()
    request, response = await app.asgi_client.websocket("/test/1")
    second_set = ev.is_set()
    assert first_set and second_set


def test_method_not_allowed(app):
    @app.route("/test", methods=["GET"])
    async def handler(request):
        return text("OK")

    request, response = app.test_client.get("/test")
    assert response.status == 200

    request, response = app.test_client.post("/test")
    assert response.status == 405


@pytest.mark.parametrize("strict_slashes", [True, False, None])
def test_static_add_route(app, strict_slashes):
    async def handler1(request):
        return text("OK1")

    async def handler2(request):
        return text("OK2")

    app.add_route(handler1, "/test", strict_slashes=strict_slashes)
    app.add_route(handler2, "/test2", strict_slashes=strict_slashes)

    request, response = app.test_client.get("/test")
    assert response.text == "OK1"

    request, response = app.test_client.get("/test2")
    assert response.text == "OK2"


def test_dynamic_add_route(app):

    results = []

    async def handler(request, name):
        results.append(name)
        return text("OK")

    app.add_route(handler, "/folder/<name>")
    request, response = app.test_client.get("/folder/test123")

    assert response.text == "OK"
    assert results[0] == "test123"


def test_dynamic_add_route_string(app):

    results = []

    async def handler(request, name):
        results.append(name)
        return text("OK")

    app.add_route(handler, "/folder/<name:str>")
    request, response = app.test_client.get("/folder/test123")

    assert response.text == "OK"
    assert results[0] == "test123"

    request, response = app.test_client.get("/folder/favicon.ico")

    assert response.text == "OK"
    assert results[1] == "favicon.ico"


def test_dynamic_add_route_int(app):
    results = []

    async def handler(request, folder_id):
        results.append(folder_id)
        return text("OK")

    app.add_route(handler, "/folder/<folder_id:int>")

    request, response = app.test_client.get("/folder/12345")
    assert response.text == "OK"
    assert type(results[0]) is int

    request, response = app.test_client.get("/folder/asdf")
    assert response.status == 404


def test_dynamic_add_route_number(app):
    results = []

    async def handler(request, weight):
        results.append(weight)
        return text("OK")

    app.add_route(handler, "/weight/<weight:float>")

    request, response = app.test_client.get("/weight/12345")
    assert response.text == "OK"
    assert type(results[0]) is float

    request, response = app.test_client.get("/weight/1234.56")
    assert response.status == 200

    request, response = app.test_client.get("/weight/.12")
    assert response.status == 200

    request, response = app.test_client.get("/weight/12.")
    assert response.status == 200

    request, response = app.test_client.get("/weight/1234-56")
    assert response.status == 404

    request, response = app.test_client.get("/weight/12.34.56")
    assert response.status == 404


def test_dynamic_add_route_regex(app):
    async def handler(request, folder_id):
        return text("OK")

    app.add_route(handler, "/folder/<folder_id:[A-Za-z0-9]{0,4}>")

    request, response = app.test_client.get("/folder/test")
    assert response.status == 200

    request, response = app.test_client.get("/folder/test1")
    assert response.status == 404

    request, response = app.test_client.get("/folder/test-123")
    assert response.status == 404

    request, response = app.test_client.get("/folder/")
    assert response.status == 200


def test_dynamic_add_route_unhashable(app):
    async def handler(request, unhashable):
        return text("OK")

    app.add_route(handler, "/folder/<unhashable:[A-Za-z0-9/]+>/end/")

    request, response = app.test_client.get("/folder/test/asdf/end/")
    assert response.status == 200

    request, response = app.test_client.get("/folder/test///////end/")
    assert response.status == 200

    request, response = app.test_client.get("/folder/test/end/")
    assert response.status == 200

    request, response = app.test_client.get("/folder/test/nope/")
    assert response.status == 404


def test_add_route_duplicate(app):

    with pytest.raises(RouteExists):

        async def handler1(request):
            pass

        async def handler2(request):
            pass

        app.add_route(handler1, "/test")
        app.add_route(handler2, "/test")

    with pytest.raises(RouteExists):

        async def handler1(request, dynamic):
            pass

        async def handler2(request, dynamic):
            pass

        app.add_route(handler1, "/test/<dynamic>/")
        app.add_route(handler2, "/test/<dynamic>/")


def test_add_route_method_not_allowed(app):
    async def handler(request):
        return text("OK")

    app.add_route(handler, "/test", methods=["GET"])

    request, response = app.test_client.get("/test")
    assert response.status == 200

    request, response = app.test_client.post("/test")
    assert response.status == 405


def test_removing_slash(app):
    @app.get("/rest/<resource>")
    def get(_):
        pass

    @app.post("/rest/<resource>")
    def post(_):
        pass

    assert len(app.router.routes_all.keys()) == 1


def test_overload_routes(app):
    @app.route("/overload", methods=["GET"])
    async def handler1(request):
        return text("OK1")

    @app.route("/overload", methods=["POST", "PUT"])
    async def handler2(request):
        return text("OK2")

    request, response = app.test_client.get("/overload")
    assert response.text == "OK1"

    request, response = app.test_client.post("/overload")
    assert response.text == "OK2"

    request, response = app.test_client.put("/overload")
    assert response.text == "OK2"

    request, response = app.test_client.delete("/overload")
    assert response.status == 405

    app.router.reset()
    with pytest.raises(RouteExists):

        @app.route("/overload", methods=["PUT", "DELETE"])
        async def handler3(request):
            return text("Duplicated")


def test_unmergeable_overload_routes(app):
    @app.route("/overload_whole", methods=None)
    async def handler1(request):
        return text("OK1")

    @app.route("/overload_whole", methods=["POST", "PUT"])
    async def handler2(request):
        return text("OK1")

    assert len(app.router.static_routes) == 1
    assert len(app.router.static_routes[("overload_whole",)].methods) == 3

    request, response = app.test_client.get("/overload_whole")
    assert response.text == "OK1"

    request, response = app.test_client.post("/overload_whole")
    assert response.text == "OK1"

    request, response = app.test_client.put("/overload_whole")
    assert response.text == "OK1"

    app.router.reset()

    @app.route("/overload_part", methods=["GET"])
    async def handler3(request):
        return text("OK1")

    with pytest.raises(RouteExists):

        @app.route("/overload_part")
        async def handler4(request):
            return text("Duplicated")

    request, response = app.test_client.get("/overload_part")
    assert response.text == "OK1"

    request, response = app.test_client.post("/overload_part")
    assert response.status == 405


def test_unicode_routes(app):
    @app.get("/你好")
    def handler1(request):
        return text("OK1")

    request, response = app.test_client.get("/你好")
    assert response.text == "OK1"

    app.router.reset()

    @app.route("/overload/<param>", methods=["GET"], unquote=True)
    async def handler2(request, param):
        return text("OK2 " + param)

    request, response = app.test_client.get("/overload/你好")
    assert response.text == "OK2 你好"


def test_uri_with_different_method_and_different_params(app):
    @app.route("/ads/<ad_id>", methods=["GET"])
    async def ad_get(request, ad_id):
        return json({"ad_id": ad_id})

    @app.route("/ads/<action>", methods=["POST"])
    async def ad_post(request, action):
        return json({"action": action})

    request, response = app.test_client.get("/ads/1234")
    assert response.status == 200
    assert response.json == {"ad_id": "1234"}

    request, response = app.test_client.post("/ads/post")
    assert response.status == 200
    assert response.json == {"action": "post"}


def test_uri_with_different_method_and_same_params(app):
    @app.route("/ads/<ad_id>", methods=["GET"])
    async def ad_get(request, ad_id):
        return json({"ad_id": ad_id})

    @app.route("/ads/<ad_id>", methods=["POST"])
    async def ad_post(request, ad_id):
        return json({"ad_id": ad_id})

    request, response = app.test_client.get("/ads/1234")
    assert response.status == 200
    assert response.json == {"ad_id": "1234"}

    request, response = app.test_client.post("/ads/post")
    assert response.status == 200
    assert response.json == {"ad_id": "post"}


def test_route_raise_ParameterNameConflicts(app):
    @app.get("/api/v1/<user>/<user>/")
    def handler(request, user):
        return text("OK")

    with pytest.raises(ParameterNameConflicts):
        app.router.finalize()


def test_route_invalid_host(app):

    host = 321
    with pytest.raises(ValueError) as excinfo:

        @app.get("/test", host=host)
        def handler(request):
            return text("pass")

    assert str(excinfo.value) == (
        "Expected either string or Iterable of " "host strings, not {!r}"
    ).format(host)


def test_route_with_regex_group(app):
    @app.route("/path/to/<ext:file\.(txt)>")
    async def handler(request, ext):
        return text(ext)

    _, response = app.test_client.get("/path/to/file.txt")
    assert response.text == "txt"


def test_route_with_regex_named_group(app):
    @app.route(r"/path/to/<ext:file\.(?P<ext>txt)>")
    async def handler(request, ext):
        return text(ext)

    _, response = app.test_client.get("/path/to/file.txt")
    assert response.text == "txt"


def test_route_with_regex_named_group_invalid(app):
    @app.route(r"/path/to/<ext:file\.(?P<wrong>txt)>")
    async def handler(request, ext):
        return text(ext)

    with pytest.raises(InvalidUsage) as e:
        app.router.finalize()

    assert e.match(
        re.escape("Named group (wrong) must match your named parameter (ext)")
    )


def test_route_with_regex_group_ambiguous(app):
    @app.route("/path/to/<ext:file(?:\.)(txt)>")
    async def handler(request, ext):
        return text(ext)

    with pytest.raises(InvalidUsage) as e:
        app.router.finalize()

    assert e.match(
        re.escape(
            "Could not compile pattern file(?:\.)(txt). Try using a named "
            "group instead: '(?P<ext>your_matching_group)'"
        )
    )


def test_route_with_bad_named_param(app):
    @app.route("/foo/<__bar__>")
    async def handler(request):
        return text("...")

    with pytest.raises(SanicException):
        app.router.finalize()


def test_routes_with_and_without_slash_definitions(app):
    bar = Blueprint("bar", url_prefix="bar")
    baz = Blueprint("baz", url_prefix="/baz")
    fizz = Blueprint("fizz", url_prefix="fizz/")
    buzz = Blueprint("buzz", url_prefix="/buzz/")

    instances = (
        (app, "foo"),
        (bar, "bar"),
        (baz, "baz"),
        (fizz, "fizz"),
        (buzz, "buzz"),
    )

    for instance, term in instances:
        route = f"/{term}" if isinstance(instance, Sanic) else ""

        @instance.get(route, strict_slashes=True)
        def get_without(request):
            return text(f"{term}_without")

        @instance.get(f"{route}/", strict_slashes=True)
        def get_with(request):
            return text(f"{term}_with")

        @instance.post(route, strict_slashes=True)
        def post_without(request):
            return text(f"{term}_without")

        @instance.post(f"{route}/", strict_slashes=True)
        def post_with(request):
            return text(f"{term}_with")

    app.blueprint(bar)
    app.blueprint(baz)
    app.blueprint(fizz)
    app.blueprint(buzz)

    for _, term in instances:
        _, response = app.test_client.get(f"/{term}")
        assert response.status == 200
        assert response.text == f"{term}_without"

        _, response = app.test_client.get(f"/{term}/")
        assert response.status == 200
        assert response.text == f"{term}_with"

        _, response = app.test_client.post(f"/{term}")
        assert response.status == 200
        assert response.text == f"{term}_without"

        _, response = app.test_client.post(f"/{term}/")
        assert response.status == 200
        assert response.text == f"{term}_with"


def test_added_route_ctx_kwargs(app):
    @app.route("/", ctx_foo="foo", ctx_bar=99)
    async def handler(request: Request):
        return empty()

    request, _ = app.test_client.get("/")

    assert request.route.ctx.foo == "foo"
    assert request.route.ctx.bar == 99


def test_added_bad_route_kwargs(app):
    message = "Unexpected keyword arguments: foo, bar"
    with pytest.raises(TypeError, match=message):

        @app.route("/", foo="foo", bar=99)
        async def handler(request: Request):
            ...


@pytest.mark.asyncio
async def test_added_callable_route_ctx_kwargs(app):
    def foo(*args, **kwargs):
        return "foo"

    async def bar(*args, **kwargs):
        return 99

    @app.route("/", ctx_foo=foo, ctx_bar=bar)
    async def handler(request: Request):
        return empty()

    request, _ = await app.asgi_client.get("/")

    assert request.route.ctx.foo() == "foo"
    assert await request.route.ctx.bar() == 99


@pytest.mark.asyncio
async def test_duplicate_route_deprecation(app):
    @app.route("/foo", name="duped")
    async def handler_foo(request):
        return text("...")

    @app.route("/bar", name="duped")
    async def handler_bar(request):
        return text("...")

    message = (
        r"\[DEPRECATION v23\.3\] Duplicate route names detected: "
        r"test_duplicate_route_deprecation\.duped\. In the future, "
        r"Sanic will enforce uniqueness in route naming\."
    )
    with pytest.warns(DeprecationWarning, match=message):
        await app._startup()
