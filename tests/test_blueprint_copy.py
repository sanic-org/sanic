import pytest

from sanic_routing.exceptions import RouteExists

from sanic import Blueprint, Request, Sanic
from sanic.response import text


def test_bp_copy(app: Sanic):
    bp1 = Blueprint("test_bp1", version=1)
    bp1.ctx.test = 1
    assert hasattr(bp1.ctx, "test")

    @bp1.route("/page")
    def handle_request(request):
        return text("Hello world!")

    bp2 = bp1.copy(name="test_bp2", version=2)
    assert id(bp1) != id(bp2)
    assert bp1._apps == bp2._apps == set()
    assert not hasattr(bp2.ctx, "test")
    assert len(bp2._future_exceptions) == len(bp1._future_exceptions)
    assert len(bp2._future_listeners) == len(bp1._future_listeners)
    assert len(bp2._future_middleware) == len(bp1._future_middleware)
    assert len(bp2._future_routes) == len(bp1._future_routes)
    assert len(bp2._future_signals) == len(bp1._future_signals)

    app.blueprint(bp1)
    app.blueprint(bp2)

    bp3 = bp1.copy(name="test_bp3", version=3, with_registration=True)
    assert id(bp1) != id(bp3)
    assert bp1._apps == bp3._apps and bp3._apps
    assert not hasattr(bp3.ctx, "test")

    bp4 = bp1.copy(name="test_bp4", version=4, with_ctx=True)
    assert id(bp1) != id(bp4)
    assert bp4.ctx.test == 1

    bp5 = bp1.copy(name="test_bp5", version=5, with_registration=False)
    assert id(bp1) != id(bp5)
    assert not bp5._apps
    assert bp1._apps != set()

    app.blueprint(bp5)

    bp6 = bp1.copy(
        name="test_bp6",
        version=6,
        with_registration=True,
        version_prefix="/version",
    )
    assert bp6._apps
    assert bp6.version_prefix == "/version"

    _, response = app.test_client.get("/v1/page")
    assert "Hello world!" in response.text

    _, response = app.test_client.get("/v2/page")
    assert "Hello world!" in response.text

    _, response = app.test_client.get("/v3/page")
    assert "Hello world!" in response.text

    _, response = app.test_client.get("/v4/page")
    assert "Hello world!" in response.text

    _, response = app.test_client.get("/v5/page")
    assert "Hello world!" in response.text

    _, response = app.test_client.get("/version6/page")
    assert "Hello world!" in response.text

    route_names = [route.name for route in app.router.routes]
    assert "test_bp_copy.test_bp1.handle_request" in route_names
    assert "test_bp_copy.test_bp2.handle_request" in route_names
    assert "test_bp_copy.test_bp3.handle_request" in route_names
    assert "test_bp_copy.test_bp4.handle_request" in route_names
    assert "test_bp_copy.test_bp5.handle_request" in route_names
    assert "test_bp_copy.test_bp6.handle_request" in route_names


def test_bp_copy_without_route_overwriting(app: Sanic):
    bpv1 = Blueprint("bp_v1", version=1, url_prefix="my_api")

    @bpv1.route("/")
    async def handler(request: Request):
        return text("v1")

    app.blueprint(bpv1)

    bpv2 = bpv1.copy("bp_v2", version=2, allow_route_overwrite=False)
    bpv3 = bpv1.copy(
        "bp_v3",
        version=3,
        allow_route_overwrite=False,
        with_registration=False,
    )

    with pytest.raises(RouteExists, match="Route already registered*"):

        @bpv2.route("/")
        async def handler(request: Request):
            return text("v2")

        app.blueprint(bpv2)

    with pytest.raises(RouteExists, match="Route already registered*"):

        @bpv3.route("/")
        async def handler(request: Request):
            return text("v3")

        app.blueprint(bpv3)


def test_bp_copy_with_route_overwriting(app: Sanic):
    bpv1 = Blueprint("bp_v1", version=1, url_prefix="my_api")

    @bpv1.route("/")
    async def handler(request: Request):
        return text("v1")

    app.blueprint(bpv1)

    bpv2 = bpv1.copy("bp_v2", version=2, allow_route_overwrite=True)
    bpv3 = bpv1.copy(
        "bp_v3", version=3, allow_route_overwrite=True, with_registration=False
    )

    @bpv2.route("/")
    async def handler(request: Request):
        return text("v2")

    app.blueprint(bpv2)

    @bpv3.route("/")
    async def handler(request: Request):
        return text("v3")

    app.blueprint(bpv3)

    _, response = app.test_client.get("/v1/my_api")
    assert response.status == 200
    assert response.text == "v1"

    _, response = app.test_client.get("/v2/my_api")
    assert response.status == 200
    assert response.text == "v2"

    _, response = app.test_client.get("/v3/my_api")
    assert response.status == 200
    assert response.text == "v3"
