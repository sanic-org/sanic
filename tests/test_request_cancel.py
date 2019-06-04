import asyncio
import contextlib

import pytest

from sanic.response import stream, text


@pytest.mark.asyncio
async def test_request_cancel_when_connection_lost(app):
    app.still_serving_cancelled_request = False

    @app.get("/")
    async def handler(request):
        await asyncio.sleep(1.0)
        # at this point client is already disconnected
        app.still_serving_cancelled_request = True
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

    assert app.still_serving_cancelled_request is False


@pytest.mark.asyncio
async def test_stream_request_cancel_when_conn_lost(app):
    app.still_serving_cancelled_request = False

    @app.post("/post/<id>", stream=True)
    async def post(request, id):
        assert isinstance(request.stream, asyncio.Queue)

        async def streaming(response):
            while True:
                body = await request.stream.get()
                if body is None:
                    break
                await response.write(body.decode("utf-8"))

        await asyncio.sleep(1.0)
        # at this point client is already disconnected
        app.still_serving_cancelled_request = True

        return stream(streaming)

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

    assert app.still_serving_cancelled_request is False
