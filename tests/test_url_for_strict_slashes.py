import asyncio

from sanic.blueprints import Blueprint


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
