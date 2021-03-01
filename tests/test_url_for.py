import asyncio

import pytest

from sanic_testing.testing import SanicTestClient

from sanic.blueprints import Blueprint


def test_routes_with_host(app):
    @app.route("/", name="hostindex", host="example.com")
    @app.route("/path", name="hostpath", host="path.example.com")
    def index(request):
        pass

    assert app.url_for("hostindex") == "/"
    assert app.url_for("hostpath") == "/path"
    assert app.url_for("hostindex", _external=True) == "http://example.com/"
    assert (
        app.url_for("hostpath", _external=True)
        == "http://path.example.com/path"
    )


def test_routes_with_multiple_hosts(app):
    @app.route("/", name="hostindex", host=["example.com", "path.example.com"])
    def index(request):
        pass

    assert app.url_for("hostindex") == "/"
    assert (
        app.url_for("hostindex", _host="example.com") == "http://example.com/"
    )

    with pytest.raises(ValueError) as e:
        assert app.url_for("hostindex", _external=True)
    assert str(e.value).startswith("Host is ambiguous")

    with pytest.raises(ValueError) as e:
        assert app.url_for("hostindex", _host="unknown.com")
    assert str(e.value).startswith(
        "Requested host (unknown.com) is not available for this route"
    )


def test_websocket_bp_route_name(app):
    """Tests that blueprint websocket route is named."""
    event = asyncio.Event()
    bp = Blueprint("test_bp", url_prefix="/bp")

    @bp.get("/main")
    async def main(request):
        ...

    @bp.websocket("/route")
    async def test_route(request, ws):
        event.set()

    @bp.websocket("/route2")
    async def test_route2(request, ws):
        event.set()

    @bp.websocket("/route3", name="foobar_3")
    async def test_route3(request, ws):
        event.set()

    app.blueprint(bp)

    uri = app.url_for("test_bp.main")
    assert uri == "/bp/main"

    uri = app.url_for("test_bp.test_route")
    assert uri == "/bp/route"
    request, response = SanicTestClient(app).websocket(uri)
    assert response.opened is True
    assert event.is_set()

    event.clear()
    uri = app.url_for("test_bp.test_route2")
    assert uri == "/bp/route2"
    request, response = SanicTestClient(app).websocket(uri)
    assert response.opened is True
    assert event.is_set()

    uri = app.url_for("test_bp.foobar_3")
    assert uri == "/bp/route3"


# TODO: add test with a route with multiple hosts
# TODO: add test with a route with _host in url_for
@pytest.mark.parametrize(
    "path,strict,expected",
    (
        ("/foo", False, "/foo"),
        ("/foo/", False, "/foo"),
        ("/foo", True, "/foo"),
        ("/foo/", True, "/foo/"),
    ),
)
def test_trailing_slash_url_for(app, path, strict, expected):
    @app.route(path, strict_slashes=strict)
    def handler(*_):
        ...

    url = app.url_for("handler")
    assert url == expected
