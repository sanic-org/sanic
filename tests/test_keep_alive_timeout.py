import asyncio
import platform

from asyncio import sleep as aio_sleep
from itertools import count
from os import environ

import pytest

from sanic_testing.reusable import ReusableClient

from sanic import Sanic
from sanic.compat import OS_IS_WINDOWS
from sanic.response import text


CONFIG_FOR_TESTS = {"KEEP_ALIVE_TIMEOUT": 2, "KEEP_ALIVE": True}

PORT = 42001  # test_keep_alive_timeout_reuse doesn't work with random port
MAX_LOOPS = 15
port_counter = count()


def get_port():
    return next(port_counter) + PORT


keep_alive_timeout_app_reuse = Sanic("test_ka_timeout_reuse")
keep_alive_app_client_timeout = Sanic("test_ka_client_timeout")
keep_alive_app_server_timeout = Sanic("test_ka_server_timeout")
keep_alive_app_context = Sanic("keep_alive_app_context")

keep_alive_timeout_app_reuse.config.update(CONFIG_FOR_TESTS)
keep_alive_app_client_timeout.config.update(CONFIG_FOR_TESTS)
keep_alive_app_server_timeout.config.update(CONFIG_FOR_TESTS)
keep_alive_app_context.config.update(CONFIG_FOR_TESTS)


@keep_alive_timeout_app_reuse.route("/1")
async def handler1(request):
    return text("OK")


@keep_alive_app_client_timeout.route("/1")
async def handler2(request):
    return text("OK")


@keep_alive_app_server_timeout.route("/1")
async def handler3(request):
    return text("OK")


@keep_alive_app_context.post("/ctx")
def set_ctx(request):
    request.conn_info.ctx.foo = "hello"
    return text("OK")


@keep_alive_app_context.get("/ctx")
def get_ctx(request):
    return text(request.conn_info.ctx.foo)


@pytest.mark.skipif(
    bool(environ.get("SANIC_NO_UVLOOP")) or OS_IS_WINDOWS,
    reason="Not testable with current client",
)
def test_keep_alive_timeout_reuse():
    """If the server keep-alive timeout and client keep-alive timeout are
    both longer than the delay, the client _and_ server will successfully
    reuse the existing connection."""
    loops = 0
    while True:
        port = get_port()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        client = ReusableClient(
            keep_alive_timeout_app_reuse, loop=loop, port=port
        )
        try:
            with client:
                headers = {"Connection": "keep-alive"}
                request, response = client.get("/1", headers=headers)
                assert response.status == 200
                assert response.text == "OK"
                assert request.protocol.state["requests_count"] == 1

                loop.run_until_complete(aio_sleep(1))

                request, response = client.get("/1")
                assert response.status == 200
                assert response.text == "OK"
                assert request.protocol.state["requests_count"] == 2
        except OSError:
            loops += 1
            if loops > MAX_LOOPS:
                raise
            continue
        else:
            break


@pytest.mark.skipif(
    bool(environ.get("SANIC_NO_UVLOOP"))
    or OS_IS_WINDOWS
    or platform.system() != "Linux",
    reason="Not testable with current client",
)
def test_keep_alive_client_timeout():
    """If the server keep-alive timeout is longer than the client
    keep-alive timeout, client will try to create a new connection here."""
    loops = 0
    while True:
        try:
            port = get_port()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            client = ReusableClient(
                keep_alive_app_client_timeout, loop=loop, port=port
            )
            with client:
                headers = {"Connection": "keep-alive"}
                request, response = client.get(
                    "/1", headers=headers, timeout=1
                )

                assert response.status == 200
                assert response.text == "OK"
                assert request.protocol.state["requests_count"] == 1

                loop.run_until_complete(aio_sleep(2))
                request, response = client.get("/1", timeout=1)
                assert request.protocol.state["requests_count"] == 1
        except OSError:
            loops += 1
            if loops > MAX_LOOPS:
                raise
            continue
        else:
            break


@pytest.mark.skipif(
    bool(environ.get("SANIC_NO_UVLOOP")) or OS_IS_WINDOWS,
    reason="Not testable with current client",
)
def test_keep_alive_server_timeout():
    """If the client keep-alive timeout is longer than the server
    keep-alive timeout, the client will either a 'Connection reset' error
    _or_ a new connection. Depending on how the event-loop handles the
    broken server connection."""
    loops = 0
    while True:
        try:
            port = get_port()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            client = ReusableClient(
                keep_alive_app_server_timeout, loop=loop, port=port
            )
            with client:
                headers = {"Connection": "keep-alive"}
                request, response = client.get(
                    "/1", headers=headers, timeout=60
                )

                assert response.status == 200
                assert response.text == "OK"
                assert request.protocol.state["requests_count"] == 1

                loop.run_until_complete(aio_sleep(3))
                request, response = client.get("/1", timeout=60)

                assert request.protocol.state["requests_count"] == 1
        except OSError:
            loops += 1
            if loops > MAX_LOOPS:
                raise
            continue
        else:
            break


@pytest.mark.skipif(
    bool(environ.get("SANIC_NO_UVLOOP")) or OS_IS_WINDOWS,
    reason="Not testable with current client",
)
def test_keep_alive_connection_context():
    loops = 0
    while True:
        try:
            port = get_port()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            client = ReusableClient(
                keep_alive_app_context, loop=loop, port=port
            )
            with client:
                headers = {"Connection": "keep-alive"}
                request1, _ = client.post("/ctx", headers=headers)

                loop.run_until_complete(aio_sleep(1))
                request2, response = client.get("/ctx")

                assert response.text == "hello"
                assert id(request1.conn_info.ctx) == id(request2.conn_info.ctx)
                assert (
                    request1.conn_info.ctx.foo
                    == request2.conn_info.ctx.foo
                    == "hello"
                )
                assert request2.protocol.state["requests_count"] == 2
        except OSError:
            loops += 1
            if loops > MAX_LOOPS:
                raise
            continue
        else:
            break
