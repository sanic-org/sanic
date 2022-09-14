from multiprocessing import Event
from os import environ, getpid
from typing import Any, Dict
from unittest.mock import Mock

import pytest

from sanic import Sanic
from sanic.worker.multiplexer import WorkerMultiplexer
from sanic.worker.state import WorkerState


@pytest.fixture
def monitor_publisher():
    return Mock()


@pytest.fixture
def worker_state():
    return {}


@pytest.fixture
def m(monitor_publisher, worker_state):
    environ["SANIC_WORKER_NAME"] = "Test"
    worker_state["Test"] = {}
    yield WorkerMultiplexer(monitor_publisher, worker_state)
    del environ["SANIC_WORKER_NAME"]


def test_has_multiplexer_default(app: Sanic):
    event = Event()

    @app.main_process_start
    async def setup(app, _):
        app.shared_ctx.event = event

    @app.after_server_start
    def stop(app):
        if hasattr(app, "m") and isinstance(app.m, WorkerMultiplexer):
            app.shared_ctx.event.set()
        app.stop()

    app.run()

    assert event.is_set()


def test_not_have_multiplexer_single(app: Sanic):
    event = Event()

    @app.main_process_start
    async def setup(app, _):
        app.shared_ctx.event = event

    @app.after_server_start
    def stop(app):
        if hasattr(app, "m") and isinstance(app.m, WorkerMultiplexer):
            app.shared_ctx.event.set()
        app.stop()

    app.run(single_process=True)

    assert not event.is_set()


def test_not_have_multiplexer_legacy(app: Sanic):
    event = Event()

    @app.main_process_start
    async def setup(app, _):
        app.shared_ctx.event = event

    @app.after_server_start
    def stop(app):
        if hasattr(app, "m") and isinstance(app.m, WorkerMultiplexer):
            app.shared_ctx.event.set()
        app.stop()

    app.run(legacy=True)

    assert not event.is_set()


def test_ack(worker_state: Dict[str, Any], m: WorkerMultiplexer):
    worker_state["Test"] = {"foo": "bar"}
    m.ack()
    assert worker_state["Test"] == {"foo": "bar", "state": "ACKED"}


def test_restart_self(monitor_publisher: Mock, m: WorkerMultiplexer):
    m.restart()
    monitor_publisher.send.assert_called_once_with("Test")


def test_restart_foo(monitor_publisher: Mock, m: WorkerMultiplexer):
    m.restart("foo")
    monitor_publisher.send.assert_called_once_with("foo")


def test_reload_alias(monitor_publisher: Mock, m: WorkerMultiplexer):
    m.reload()
    monitor_publisher.send.assert_called_once_with("Test")


def test_terminate(monitor_publisher: Mock, m: WorkerMultiplexer):
    m.terminate()
    monitor_publisher.send.assert_called_once_with("__TERMINATE__")


def test_properties(
    monitor_publisher: Mock, worker_state: Dict[str, Any], m: WorkerMultiplexer
):
    assert m.reload == m.restart
    assert m.pid == getpid()
    assert m.name == "Test"
    assert m.workers == worker_state
    assert m.state == worker_state["Test"]
    assert isinstance(m.state, WorkerState)
