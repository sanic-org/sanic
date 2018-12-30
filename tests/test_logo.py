import logging
import asyncio
import pytest

from sanic.config import BASE_LOGO


@pytest.fixture
def server(app):
    server = app.create_server(debug=True)
    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(server)
    return loop, task


def test_logo_base(app, server, caplog):
    loop, task = server
    with caplog.at_level(logging.DEBUG):
        runner = loop.run_until_complete(task)
        runner.close()

    assert caplog.record_tuples[0] == ("sanic.root", logging.DEBUG, BASE_LOGO)


def test_logo_false(app, server, caplog):
    app.config.LOGO = False
    loop, task = server
    with caplog.at_level(logging.DEBUG):
        runner = loop.run_until_complete(task)
        runner.close()

    assert caplog.record_tuples[0] == (
        "sanic.root",
        logging.INFO,
        "Goin' Fast @ http://127.0.0.1:8000",
    )


def test_logo_true(app, server, caplog):
    app.config.LOGO = True
    loop, task = server
    with caplog.at_level(logging.DEBUG):
        runner = loop.run_until_complete(task)
        runner.close()

    assert caplog.record_tuples[0] == ("sanic.root", logging.DEBUG, BASE_LOGO)


def test_logo_custom(app, server, caplog):
    app.config.LOGO = "My Custom Logo"
    loop, task = server
    with caplog.at_level(logging.DEBUG):
        runner = loop.run_until_complete(task)
        runner.close()

    assert caplog.record_tuples[0] == (
        "sanic.root",
        logging.DEBUG,
        "My Custom Logo",
    )
