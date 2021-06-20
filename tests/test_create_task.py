import asyncio

from threading import Event

import pytest

from sanic.response import text


def test_create_task(app):
    e = Event()

    async def coro():
        await asyncio.sleep(0.05)
        e.set()

    app.add_task(coro)

    @app.route("/early")
    def not_set(request):
        return text(str(e.is_set()))

    @app.route("/late")
    async def set(request):
        await asyncio.sleep(0.1)
        return text(str(e.is_set()))

    request, response = app.test_client.get("/early")
    assert response.body == b"False"

    request, response = app.test_client.get("/late")
    assert response.body == b"True"


@pytest.mark.asyncio
async def test_create_task_with_app_arg(app):
    q = asyncio.Queue()

    @app.route("/")
    def not_set(request):
        return "hello"

    async def coro(app):
        await q.put(app.name)

    app.add_task(coro)

    request, response = await app.asgi_client.get("/")
    # assert await q.get() == "test_create_task_with_app_arg"
