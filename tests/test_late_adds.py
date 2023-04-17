import pytest

from sanic import Sanic, text


@pytest.fixture
def late_app(app: Sanic):
    app.config.TOUCHUP = False
    app.get("/")(lambda _: text(""))
    return app


def test_late_route(late_app: Sanic):
    @late_app.before_server_start
    async def late(app: Sanic):
        @app.get("/late")
        def handler(_):
            return text("late")

    _, response = late_app.test_client.get("/late")
    assert response.status_code == 200
    assert response.text == "late"


def test_late_middleware(late_app: Sanic):
    @late_app.get("/late")
    def handler(request):
        return text(request.ctx.late)

    @late_app.before_server_start
    async def late(app: Sanic):
        @app.on_request
        def handler(request):
            request.ctx.late = "late"

    _, response = late_app.test_client.get("/late")
    assert response.status_code == 200
    assert response.text == "late"


def test_late_signal(late_app: Sanic):
    @late_app.get("/late")
    def handler(request):
        return text(request.ctx.late)

    @late_app.before_server_start
    async def late(app: Sanic):
        @app.signal("http.lifecycle.request")
        def handler(request):
            request.ctx.late = "late"

    _, response = late_app.test_client.get("/late")
    assert response.status_code == 200
    assert response.text == "late"
