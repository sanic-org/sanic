import asyncio
import logging

from pytest import LogCaptureFixture

from sanic.response import empty


PORT = 42101


def test_no_exceptions_when_cancel_pending_request(
    app, caplog: LogCaptureFixture
):
    app.config.GRACEFUL_SHUTDOWN_TIMEOUT = 1

    @app.get("/")
    async def handler(request):
        await asyncio.sleep(5)

    @app.listener("after_server_start")
    async def _request(sanic, loop):
        connect = asyncio.open_connection("127.0.0.1", 8000)
        _, writer = await connect
        writer.write(b"GET / HTTP/1.1\r\n\r\n")
        app.stop()

    with caplog.at_level(logging.INFO):
        app.run(single_process=True, access_log=True)

    assert "Request: GET http:/// stopped. Transport is closed." in caplog.text


def test_completes_request(app, caplog: LogCaptureFixture):
    app.config.GRACEFUL_SHUTDOWN_TIMEOUT = 1

    @app.get("/")
    async def handler(request):
        await asyncio.sleep(0.5)
        return empty()

    @app.listener("after_server_start")
    async def _request(sanic, loop):
        connect = asyncio.open_connection("127.0.0.1", 8000)
        _, writer = await connect
        writer.write(b"GET / HTTP/1.1\r\n\r\n")
        app.stop()

    with caplog.at_level(logging.INFO):
        app.run(single_process=True, access_log=True)

    assert ("sanic.access", 20, "") in caplog.record_tuples

    # Make sure that the server starts shutdown process before access log
    index_stopping = 0
    for idx, record in enumerate(caplog.records):
        if record.message.startswith("Stopping worker"):
            index_stopping = idx
            break
    index_request = caplog.record_tuples.index(("sanic.access", 20, ""))
    assert index_request > index_stopping > 0
