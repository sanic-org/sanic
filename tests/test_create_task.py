import asyncio

from threading import Event

from sanic.response import text


def test_create_task(app):
    e = Event()

    async def coro():
        await asyncio.sleep(0.05)
        e.set()

    @app.route("/early")
    def not_set(request):
        return text(str(e.is_set()))

    @app.route("/late")
    async def set(request):
        await asyncio.sleep(0.1)
        return text(str(e.is_set()))

    app.add_task(coro)

    request, response = app.test_client.get("/early")
    assert response.body == b"False"

    app.signal_router.reset()
    app.add_task(coro)
    request, response = app.test_client.get("/late")
    assert response.body == b"True"


def test_create_task_with_app_arg(app):
    @app.after_server_start
    async def setup_q(app, _):
        app.ctx.q = asyncio.Queue()

    @app.route("/")
    async def not_set(request):
        return text(await request.app.ctx.q.get())

    async def coro(app):
        await app.ctx.q.put(app.name)

    app.add_task(coro)

    _, response = app.test_client.get("/")
    assert response.text == "test_create_task_with_app_arg"
