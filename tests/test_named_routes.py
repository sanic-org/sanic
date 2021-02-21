#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio

import pytest

from sanic import Sanic
from sanic.blueprints import Blueprint
from sanic.constants import HTTP_METHODS
from sanic.exceptions import URLBuildError
from sanic.response import text


# ------------------------------------------------------------ #
#  UTF-8
# ------------------------------------------------------------ #


@pytest.mark.parametrize("method", HTTP_METHODS)
def test_versioned_named_routes_get(method):
    app = Sanic("app")

    bp = Blueprint("test_bp", url_prefix="/bp")

    method = method.lower()
    route_name = f"route_{method}"
    route_name2 = f"route2_{method}"

    func = getattr(app, method)
    if callable(func):

        @func(f"/{method}", version=1, name=route_name)
        def handler(request):
            return text("OK")

    else:
        raise

    func = getattr(bp, method)
    if callable(func):

        @func(f"/{method}", version=1, name=route_name2)
        def handler2(request):
            return text("OK")

    else:
        raise

    app.blueprint(bp)

    assert (
        app.router.routes_all[
            (
                "v1",
                method,
            )
        ].name
        == f"app.{route_name}"
    )

    route = app.router.routes_all[
        (
            "v1",
            "bp",
            method,
        )
    ]
    assert route.name == f"app.test_bp.{route_name2}"

    assert app.url_for(route_name) == f"/v1/{method}"
    url = app.url_for(f"test_bp.{route_name2}")
    assert url == f"/v1/bp/{method}"
    with pytest.raises(URLBuildError):
        app.url_for("handler")


def test_shorthand_default_routes_get():
    app = Sanic("app")

    @app.get("/get")
    def handler(request):
        return text("OK")

    assert app.router.routes_all[("get",)].name == "app.handler"
    assert app.url_for("handler") == "/get"


def test_shorthand_named_routes_get():
    app = Sanic("app")
    bp = Blueprint("test_bp", url_prefix="/bp")

    @app.get("/get", name="route_get")
    def handler(request):
        return text("OK")

    @bp.get("/get", name="route_bp")
    def handler2(request):
        return text("Blueprint")

    app.blueprint(bp)

    assert app.router.routes_all[("get",)].name == "app.route_get"
    assert app.url_for("route_get") == "/get"
    with pytest.raises(URLBuildError):
        app.url_for("handler")

    assert (
        app.router.routes_all[
            (
                "bp",
                "get",
            )
        ].name
        == "app.test_bp.route_bp"
    )
    assert app.url_for("test_bp.route_bp") == "/bp/get"
    with pytest.raises(URLBuildError):
        app.url_for("test_bp.handler2")


def test_shorthand_named_routes_post():
    app = Sanic("app")

    @app.post("/post", name="route_name")
    def handler(request):
        return text("OK")

    assert app.router.routes_all[("post",)].name == "app.route_name"
    assert app.url_for("route_name") == "/post"
    with pytest.raises(URLBuildError):
        app.url_for("handler")


def test_shorthand_named_routes_put():
    app = Sanic("app")

    @app.put("/put", name="route_put")
    def handler(request):
        return text("OK")

    assert app.router.routes_all[("put",)].name == "app.route_put"
    assert app.url_for("route_put") == "/put"
    with pytest.raises(URLBuildError):
        app.url_for("handler")


def test_shorthand_named_routes_delete():
    app = Sanic("app")

    @app.delete("/delete", name="route_delete")
    def handler(request):
        return text("OK")

    assert app.router.routes_all[("delete",)].name == "app.route_delete"
    assert app.url_for("route_delete") == "/delete"
    with pytest.raises(URLBuildError):
        app.url_for("handler")


def test_shorthand_named_routes_patch():
    app = Sanic("app")

    @app.patch("/patch", name="route_patch")
    def handler(request):
        return text("OK")

    assert app.router.routes_all[("patch",)].name == "app.route_patch"
    assert app.url_for("route_patch") == "/patch"
    with pytest.raises(URLBuildError):
        app.url_for("handler")


def test_shorthand_named_routes_head():
    app = Sanic("app")

    @app.head("/head", name="route_head")
    def handler(request):
        return text("OK")

    assert app.router.routes_all[("head",)].name == "app.route_head"
    assert app.url_for("route_head") == "/head"
    with pytest.raises(URLBuildError):
        app.url_for("handler")


def test_shorthand_named_routes_options():
    app = Sanic("app")

    @app.options("/options", name="route_options")
    def handler(request):
        return text("OK")

    assert app.router.routes_all[("options",)].name == "app.route_options"
    assert app.url_for("route_options") == "/options"
    with pytest.raises(URLBuildError):
        app.url_for("handler")


def test_named_static_routes():
    app = Sanic("app")

    @app.route("/test", name="route_test")
    async def handler1(request):
        return text("OK1")

    @app.route("/pizazz", name="route_pizazz")
    async def handler2(request):
        return text("OK2")

    assert app.router.routes_all[("test",)].name == "app.route_test"
    assert app.router.routes_static[("test",)].name == "app.route_test"
    assert app.url_for("route_test") == "/test"
    with pytest.raises(URLBuildError):
        app.url_for("handler1")

    assert app.router.routes_all[("pizazz",)].name == "app.route_pizazz"
    assert app.router.routes_static[("pizazz",)].name == "app.route_pizazz"
    assert app.url_for("route_pizazz") == "/pizazz"
    with pytest.raises(URLBuildError):
        app.url_for("handler2")


def test_named_dynamic_route():
    app = Sanic("app")
    results = []

    @app.route("/folder/<name>", name="route_dynamic")
    async def handler(request, name):
        results.append(name)
        return text("OK")

    assert (
        app.router.routes_all[
            (
                "folder",
                "<name>",
            )
        ].name
        == "app.route_dynamic"
    )
    assert app.url_for("route_dynamic", name="test") == "/folder/test"
    with pytest.raises(URLBuildError):
        app.url_for("handler")


def test_dynamic_named_route_regex():
    app = Sanic("app")

    @app.route("/folder/<folder_id:[A-Za-z0-9]{0,4}>", name="route_re")
    async def handler(request, folder_id):
        return text("OK")

    route = app.router.routes_all[
        (
            "folder",
            "<folder_id:[A-Za-z0-9]{0,4}>",
        )
    ]
    assert route.name == "app.route_re"
    assert app.url_for("route_re", folder_id="test") == "/folder/test"
    with pytest.raises(URLBuildError):
        app.url_for("handler")


def test_dynamic_named_route_path():
    app = Sanic("app")

    @app.route("/<path:path>/info", name="route_dynamic_path")
    async def handler(request, path):
        return text("OK")

    route = app.router.routes_all[
        (
            "<path:path>",
            "info",
        )
    ]
    assert route.name == "app.route_dynamic_path"
    assert app.url_for("route_dynamic_path", path="path/1") == "/path/1/info"
    with pytest.raises(URLBuildError):
        app.url_for("handler")


def test_dynamic_named_route_unhashable():
    app = Sanic("app")

    @app.route(
        "/folder/<unhashable:[A-Za-z0-9/]+>/end/", name="route_unhashable"
    )
    async def handler(request, unhashable):
        return text("OK")

    route = app.router.routes_all[
        (
            "folder",
            "<unhashable:[A-Za-z0-9/]+>",
            "end",
        )
    ]
    assert route.name == "app.route_unhashable"
    url = app.url_for("route_unhashable", unhashable="test/asdf")
    assert url == "/folder/test/asdf/end"
    with pytest.raises(URLBuildError):
        app.url_for("handler")


def test_websocket_named_route():
    app = Sanic("app")
    ev = asyncio.Event()

    @app.websocket("/ws", name="route_ws")
    async def handler(request, ws):
        assert ws.subprotocol is None
        ev.set()

    assert app.router.routes_all[("ws",)].name == "app.route_ws"
    assert app.url_for("route_ws") == "/ws"
    with pytest.raises(URLBuildError):
        app.url_for("handler")


def test_websocket_named_route_with_subprotocols():
    app = Sanic("app")
    results = []

    @app.websocket("/ws", subprotocols=["foo", "bar"], name="route_ws")
    async def handler(request, ws):
        results.append(ws.subprotocol)

    assert app.router.routes_all[("ws",)].name == "app.route_ws"
    assert app.url_for("route_ws") == "/ws"
    with pytest.raises(URLBuildError):
        app.url_for("handler")


def test_static_add_named_route():
    app = Sanic("app")

    async def handler1(request):
        return text("OK1")

    async def handler2(request):
        return text("OK2")

    app.add_route(handler1, "/test", name="route_test")
    app.add_route(handler2, "/test2", name="route_test2")

    assert app.router.routes_all[("test",)].name == "app.route_test"
    assert app.router.routes_static[("test",)].name == "app.route_test"
    assert app.url_for("route_test") == "/test"
    with pytest.raises(URLBuildError):
        app.url_for("handler1")

    assert app.router.routes_all[("test2",)].name == "app.route_test2"
    assert app.router.routes_static[("test2",)].name == "app.route_test2"
    assert app.url_for("route_test2") == "/test2"
    with pytest.raises(URLBuildError):
        app.url_for("handler2")


def test_dynamic_add_named_route():
    app = Sanic("app")
    results = []

    async def handler(request, name):
        results.append(name)
        return text("OK")

    app.add_route(handler, "/folder/<name>", name="route_dynamic")
    assert (
        app.router.routes_all[("folder", "<name>")].name == "app.route_dynamic"
    )
    assert app.url_for("route_dynamic", name="test") == "/folder/test"
    with pytest.raises(URLBuildError):
        app.url_for("handler")


def test_dynamic_add_named_route_unhashable():
    app = Sanic("app")

    async def handler(request, unhashable):
        return text("OK")

    app.add_route(
        handler,
        "/folder/<unhashable:[A-Za-z0-9/]+>/end/",
        name="route_unhashable",
    )
    route = app.router.routes_all[
        (
            "folder",
            "<unhashable:[A-Za-z0-9/]+>",
            "end",
        )
    ]
    assert route.name == "app.route_unhashable"
    url = app.url_for("route_unhashable", unhashable="folder1")
    assert url == "/folder/folder1/end"
    with pytest.raises(URLBuildError):
        app.url_for("handler")


def test_overload_routes():
    app = Sanic("app")

    @app.route("/overload", methods=["GET"], name="route_first")
    async def handler1(request):
        return text("OK1")

    @app.route("/overload", methods=["POST", "PUT"], name="route_second")
    async def handler2(request):
        return text("OK2")

    request, response = app.test_client.get(app.url_for("route_first"))
    assert response.text == "OK1"

    request, response = app.test_client.post(app.url_for("route_first"))
    assert response.text == "OK2"

    request, response = app.test_client.put(app.url_for("route_first"))
    assert response.text == "OK2"

    request, response = app.test_client.get(app.url_for("route_second"))
    assert response.text == "OK1"

    request, response = app.test_client.post(app.url_for("route_second"))
    assert response.text == "OK2"

    request, response = app.test_client.put(app.url_for("route_second"))
    assert response.text == "OK2"

    assert app.router.routes_all[("overload",)].name == "app.route_first"
    with pytest.raises(URLBuildError):
        app.url_for("handler1")

    assert app.url_for("route_first") == "/overload"
    assert app.url_for("route_second") == app.url_for("route_first")
