import logging

from unittest.mock import AsyncMock

import pytest

from sanic import Sanic
from sanic.response import text


@pytest.fixture
def app_one():
    app = Sanic("One")

    @app.get("/one")
    async def one(request):
        return text("one")

    return app


@pytest.fixture
def app_two():
    app = Sanic("Two")

    @app.get("/two")
    async def two(request):
        return text("two")

    return app


@pytest.fixture
def run_multi(caplog):
    def run(app):
        @app.after_server_start
        async def stop(app, _):
            app.stop()

        with caplog.at_level(logging.DEBUG):
            Sanic.serve()

        return caplog.record_tuples

    return run


def test_serve_same_app_multiple_tuples(app_one, run_multi):
    app_one.prepare(port=23456)
    app_one.prepare(port=23457)

    logs = run_multi(app_one)
    assert (
        "sanic.root",
        logging.INFO,
        "Goin' Fast @ http://127.0.0.1:23456",
    ) in logs
    assert (
        "sanic.root",
        logging.INFO,
        "Goin' Fast @ http://127.0.0.1:23457",
    ) in logs


def test_serve_multiple_apps(app_one, app_two, run_multi):
    app_one.prepare(port=23456)
    app_two.prepare(port=23457)

    logs = run_multi(app_one)
    assert (
        "sanic.root",
        logging.INFO,
        "Goin' Fast @ http://127.0.0.1:23456",
    ) in logs
    assert (
        "sanic.root",
        logging.INFO,
        "Goin' Fast @ http://127.0.0.1:23457",
    ) in logs


def test_listeners_on_secondary_app(app_one, app_two, run_multi):
    app_one.prepare(port=23456)
    app_two.prepare(port=23457)

    before_start = AsyncMock()
    after_start = AsyncMock()
    before_stop = AsyncMock()
    after_stop = AsyncMock()

    # app_two.before_server_start(before_start)
    # app_two.after_server_start(after_start)
    # app_two.before_server_stop(before_stop)
    # app_two.after_server_stop(after_stop)

    @app_two.before_server_start
    async def before_server_start(*_):
        print(">>>> before_server_start")

    run_multi(app_one)

    # before_start.assert_awaited_once()
    # after_start.assert_awaited_once()
    # before_stop.assert_awaited_once()
    # after_stop.assert_awaited_once()
