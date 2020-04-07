import asyncio
import logging

from sanic.config import BASE_LOGO
from sanic.testing import PORT


try:
    import uvloop  # noqa

    ROW = 0
except BaseException:
    ROW = 1


def test_logo_base(app, caplog):
    server = app.create_server(
        debug=True, return_asyncio_server=True, port=PORT
    )
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop._stopping = False

    with caplog.at_level(logging.DEBUG):
        _server = loop.run_until_complete(server)

    _server.close()
    loop.run_until_complete(_server.wait_closed())
    app.stop()

    assert caplog.record_tuples[ROW][1] == logging.DEBUG
    assert caplog.record_tuples[ROW][2] == BASE_LOGO


def test_logo_false(app, caplog):
    app.config.LOGO = False

    server = app.create_server(
        debug=True, return_asyncio_server=True, port=PORT
    )
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop._stopping = False

    with caplog.at_level(logging.DEBUG):
        _server = loop.run_until_complete(server)

    _server.close()
    loop.run_until_complete(_server.wait_closed())
    app.stop()

    banner, port = caplog.record_tuples[ROW][2].rsplit(":", 1)
    assert caplog.record_tuples[ROW][1] == logging.INFO
    assert banner == "Goin' Fast @ http://127.0.0.1"
    assert int(port) > 0


def test_logo_true(app, caplog):
    app.config.LOGO = True

    server = app.create_server(
        debug=True, return_asyncio_server=True, port=PORT
    )
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop._stopping = False

    with caplog.at_level(logging.DEBUG):
        _server = loop.run_until_complete(server)

    _server.close()
    loop.run_until_complete(_server.wait_closed())
    app.stop()

    assert caplog.record_tuples[ROW][1] == logging.DEBUG
    assert caplog.record_tuples[ROW][2] == BASE_LOGO


def test_logo_custom(app, caplog):
    app.config.LOGO = "My Custom Logo"

    server = app.create_server(
        debug=True, return_asyncio_server=True, port=PORT
    )
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop._stopping = False

    with caplog.at_level(logging.DEBUG):
        _server = loop.run_until_complete(server)

    _server.close()
    loop.run_until_complete(_server.wait_closed())
    app.stop()

    assert caplog.record_tuples[ROW][1] == logging.DEBUG
    assert caplog.record_tuples[ROW][2] == "My Custom Logo"
