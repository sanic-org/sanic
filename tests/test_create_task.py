import asyncio

from threading import Event

import pytest

from sanic.exceptions import SanicException
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


def test_create_named_task(app):
    async def dummy():
        ...

    @app.before_server_start
    async def setup(app, _):
        app.add_task(dummy, name="dummy_task")

    @app.after_server_start
    async def stop(app, _):
        app.stop()

    app.run()
    task = app.get_task("dummy_task")

    assert app._task_registry
    assert isinstance(task, asyncio.Task)
    assert task.get_name() == "dummy_task"


def test_create_named_task_fails_outside_app(app):
    async def dummy():
        ...

    message = "Cannot name task outside of a running application"
    with pytest.raises(RuntimeError, match=message):
        app.add_task(dummy, name="dummy_task")
    assert not app._task_registry

    message = 'Registered task named "dummy_task" not found.'
    with pytest.raises(SanicException, match=message):
        app.get_task("dummy_task")
