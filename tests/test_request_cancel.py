import asyncio
import contextlib

import pytest

from sanic.response import text


@pytest.mark.asyncio
async def test_request_cancel_when_connection_lost(app):
    app.ctx.still_serving_cancelled_request = False

    @app.get("/")
    async def handler(request):
        await asyncio.sleep(1.0)
        # at this point client is already disconnected
        app.ctx.still_serving_cancelled_request = True
        return text("OK")

    # schedule client call
    loop = asyncio.get_event_loop()
    task = loop.create_task(app.asgi_client.get("/"))
    loop.call_later(0.01, task)
    await asyncio.sleep(0.5)

    # cancelling request and closing connection after 0.5 sec
    task.cancel()

    with contextlib.suppress(asyncio.CancelledError):
        await task

    # Wait for server and check if it's still serving the cancelled request
    await asyncio.sleep(1.0)

    assert app.ctx.still_serving_cancelled_request is False


@pytest.mark.asyncio
async def test_stream_request_cancel_when_conn_lost(app):
    app.ctx.still_serving_cancelled_request = False

    @app.post("/post/<id>", stream=True)
    async def post(request, id):
        assert isinstance(request.stream, asyncio.Queue)

        response = await request.respond()

        await asyncio.sleep(1.0)
        # at this point client is already disconnected
        app.ctx.still_serving_cancelled_request = True
        while True:
            body = await request.stream.get()
            if body is None:
                break
            await response.send(body.decode("utf-8"))

    # schedule client call
    loop = asyncio.get_event_loop()
    task = loop.create_task(app.asgi_client.post("/post/1"))
    loop.call_later(0.01, task)
    await asyncio.sleep(0.5)

    # cancelling request and closing connection after 0.5 sec
    task.cancel()

    with contextlib.suppress(asyncio.CancelledError):
        await task

    # Wait for server and check if it's still serving the cancelled request
    await asyncio.sleep(1.0)

    assert app.ctx.still_serving_cancelled_request is False
