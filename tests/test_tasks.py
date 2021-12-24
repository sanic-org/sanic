import asyncio
import sys

from asyncio.tasks import Task
from unittest.mock import Mock, call

import pytest

from sanic.app import Sanic
from sanic.response import empty


pytestmark = pytest.mark.asyncio


async def dummy(n=0):
    for _ in range(n):
        await asyncio.sleep(1)
    return True


@pytest.fixture(autouse=True)
def mark_app_running(app):
    app.is_running = True


@pytest.mark.skipif(sys.version_info < (3, 8), reason="Not supported in 3.7")
async def test_add_task_returns_task(app: Sanic):
    task = app.add_task(dummy())

    assert isinstance(task, Task)
    assert len(app._task_registry) == 0


@pytest.mark.skipif(sys.version_info < (3, 8), reason="Not supported in 3.7")
async def test_add_task_with_name(app: Sanic):
    task = app.add_task(dummy(), name="dummy")

    assert isinstance(task, Task)
    assert len(app._task_registry) == 1
    assert task is app.get_task("dummy")

    for task in app.tasks:
        assert task in app._task_registry.values()


@pytest.mark.skipif(sys.version_info < (3, 8), reason="Not supported in 3.7")
async def test_cancel_task(app: Sanic):
    task = app.add_task(dummy(3), name="dummy")

    assert task
    assert not task.done()
    assert not task.cancelled()

    await asyncio.sleep(0.1)

    assert not task.done()
    assert not task.cancelled()

    await app.cancel_task("dummy")

    assert task.cancelled()


@pytest.mark.skipif(sys.version_info < (3, 8), reason="Not supported in 3.7")
async def test_purge_tasks(app: Sanic):
    app.add_task(dummy(3), name="dummy")

    await app.cancel_task("dummy")

    assert len(app._task_registry) == 1

    app.purge_tasks()

    assert len(app._task_registry) == 0


@pytest.mark.skipif(sys.version_info < (3, 8), reason="Not supported in 3.7")
def test_shutdown_tasks_on_app_stop():
    class TestSanic(Sanic):
        shutdown_tasks = Mock()

    app = TestSanic("Test")

    @app.route("/")
    async def handler(_):
        return empty()

    app.test_client.get("/")

    app.shutdown_tasks.call_args == [
        call(timeout=0),
        call(15.0),
    ]
