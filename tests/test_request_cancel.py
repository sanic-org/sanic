import pytest
import asyncio
import contextlib

from sanic.response import text


async def test_request_cancel_when_connection_lost(loop, app, test_client):
    app.still_serving_cancelled_request = False

    @app.get('/')
    async def handler(request):
        await asyncio.sleep(1.0)
        # at this point client is already disconnected
        app.still_serving_cancelled_request = True
        return text('OK')

    test_cli = await test_client(app)

    # schedule client call
    task = loop.create_task(test_cli.get('/'))
    loop.call_later(0.01, task)
    await asyncio.sleep(0.5)

    # cancelling request and closing connection after 0.5 sec
    task.cancel()

    with contextlib.suppress(asyncio.CancelledError):
        await task

    # Wait for server and check if it's still serving the cancelled request
    await asyncio.sleep(1.0)

    assert app.still_serving_cancelled_request is False
