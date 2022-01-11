import logging

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
