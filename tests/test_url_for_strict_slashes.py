import asyncio
from collections import OrderedDict
from functools import partial
from itertools import product
import pytest

from sanic import Sanic
from sanic.blueprints import Blueprint
from sanic.response import text
from sanic.constants import HTTP_METHODS


def pytest_generate_tests(metafunc):
    """Generate params.

    called once per each test function
    """
    if metafunc.cls is not None:
        params = metafunc.cls.get_params(metafunc.function.__name__)
        metafunc.parametrize(
            list(params[0].keys()),
            [list(funcargs.values()) for funcargs in params],
        )


def test_websocket_bp_route_wraps(app):
    """Tests that blueprint websocket route is wrapped."""
    event = asyncio.Event()
    bp = Blueprint("test_bp", url_prefix="/bp")

    @bp.websocket("/route")
    async def test_route(request, ws):
        event.set()

    @bp.websocket("/route2")
    async def test_route2(request, ws):
        event.set()

    app.blueprint(bp)

    uri = app.url_for("test_bp.test_route")
    assert uri == "/bp/route"
    request, response = app.test_client.websocket(uri)
    assert response.opened is True
    assert event.is_set()

    event.clear()
    uri2 = app.url_for("test_bp.test_route2")
    assert uri2 == "/bp/route2"
    request, response = app.test_client.websocket(uri2)
    assert response.opened is True
    assert event.is_set()


class TestStrictSlashes:
    """All cases."""

    @staticmethod
    def get_params(function_name):
        fabric_app = partial(Sanic, "test")
        all_bp = [None, partial(Blueprint, "test_bp", url_prefix="/bp")]
        all_routes = ["/route", "/route/"]
        all_slashes = [None, False, True]
        all_decorated = [False, True]
        all_methods = HTTP_METHODS

        if function_name == "test_websocket_bp_route":
            all_methods = ["websocket"]
        packed = [all_bp, all_routes, all_methods, all_decorated,
                  all_slashes, all_slashes, all_slashes]

        params = []

        for (fabric_bp, route_uri, http_method, decorated, app_strict_slashes,
             bp_strict_slashes, route_strict_slashes) in product(*packed):

            app = fabric_app(strict_slashes=app_strict_slashes)
            bp = None
            if fabric_bp is None:
                if bp_strict_slashes is not None:
                    continue
            else:
                bp = fabric_bp(strict_slashes=bp_strict_slashes)

            slashes = [app_strict_slashes, bp_strict_slashes,
                       route_strict_slashes]

            # default is 200 - OK
            resp = 200
            resp_with_slash = 200

            while slashes:
                slash = slashes.pop()
                if slash is None:
                    # skip all default
                    continue
                if slash is True:
                    # if last was strict
                    if route_uri.endswith("/"):
                        # "/route/", strict_slashes=True
                        resp = 404
                    else:
                        # "/route", strict_slashes=True
                        resp_with_slash = 404
                break

            param_row = OrderedDict(
                app=app,
                bp=bp,
                route_uri=route_uri,
                http_method=http_method,
                decorated=decorated,
                app_strict_slashes=app_strict_slashes,
                bp_strict_slashes=bp_strict_slashes,
                route_strict_slashes=route_strict_slashes,
                resp=resp,
                resp_with_slash=resp_with_slash,
            )
            params.append(param_row)

        return params

    # @pytest.mark.skip
    def test_websocket_bp_route(self, app, bp, route_uri, http_method,
                                decorated, app_strict_slashes,
                                bp_strict_slashes, route_strict_slashes,
                                resp, resp_with_slash):
        """Websocket app route with optional blueprint."""
        event = asyncio.Event()

        if bp:
            if decorated:
                @bp.websocket(route_uri, strict_slashes=route_strict_slashes)
                async def sample_route(request, ws):
                    event.set()
            else:
                async def sample_route(request, ws):
                    event.set()

                bp.add_websocket_route(sample_route, route_uri,
                                       strict_slashes=route_strict_slashes)

            app.blueprint(bp)
        else:
            if decorated:
                @app.websocket(route_uri, strict_slashes=route_strict_slashes)
                async def sample_route(request, ws):
                    event.set()
            else:
                async def sample_route(request, ws):
                    event.set()

                app.add_websocket_route(sample_route, route_uri,
                              strict_slashes=route_strict_slashes)

        client_method = getattr(app.test_client, http_method.lower())

        route_name = "sample_route"
        expected_uri = route_uri.rstrip("/")

        if bp:
            route_name = "test_bp." + route_name
            expected_uri = "/bp" + expected_uri

        uri = app.url_for(route_name)
        assert uri == expected_uri

        if resp == 200:
            _, response = client_method(uri)
            assert response.opened is True
            assert event.is_set()
        else:
            with pytest.raises(ValueError) as excinfo:
                _, response = app.test_client.websocket(uri)
                assert "HTTP 404" in excinfo.value

        uri_with_slash = uri + "/"
        event.clear()

        if resp_with_slash == 200:
            _, response = client_method(uri_with_slash)
            assert response.opened is True
            assert event.is_set()
        else:
            with pytest.raises(ValueError) as excinfo:
                _, response = app.test_client.websocket(uri_with_slash)
                assert "HTTP 404" in excinfo.value

    # @pytest.mark.skip
    def test_http_bp_route(self, app, bp, route_uri, http_method, decorated,
                           app_strict_slashes, bp_strict_slashes,
                           route_strict_slashes, resp, resp_with_slash):
        """HTTP app route with optional blueprint."""
        if bp:
            if decorated:
                @bp.route(route_uri, methods=[http_method],
                          strict_slashes=route_strict_slashes)
                async def sample_route(request):
                    return text("OK")
            else:
                async def sample_route(request):
                    return text("OK")

                bp.add_route(sample_route, route_uri, methods=[http_method],
                             strict_slashes=route_strict_slashes)

            app.blueprint(bp)
        else:
            if decorated:
                @app.route(route_uri, methods=[http_method],
                           strict_slashes=route_strict_slashes)
                async def sample_route(request):
                    return text("OK")
            else:
                async def sample_route(request):
                    return text("OK")

                app.add_route(sample_route, route_uri, methods=[http_method],
                              strict_slashes=route_strict_slashes)

        client_method = getattr(app.test_client, http_method.lower())

        route_name = "sample_route"
        expected_uri = route_uri.rstrip("/")

        if bp:
            route_name = "test_bp." + route_name
            expected_uri = "/bp" + expected_uri

        uri = app.url_for(route_name)
        assert uri == expected_uri

        _, response = client_method(uri)
        assert response.status == resp

        uri_with_slash = uri + "/"

        _, response = client_method(uri_with_slash)
        assert response.status == resp_with_slash
