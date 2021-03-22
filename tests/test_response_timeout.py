import asyncio

from time import sleep

from sanic import Sanic
from sanic.exceptions import ServiceUnavailable
from sanic.response import text


response_timeout_app = Sanic("test_response_timeout")
response_timeout_default_app = Sanic("test_response_timeout_default")
response_handler_cancelled_app = Sanic("test_response_handler_cancelled")
response_ws_app = Sanic("response_ws_app")

response_timeout_app.config.RESPONSE_TIMEOUT = 1
response_timeout_default_app.config.RESPONSE_TIMEOUT = 1
response_handler_cancelled_app.config.RESPONSE_TIMEOUT = 1
response_ws_app.config.RESPONSE_TIMEOUT = 1

response_ws_app.ctx.event = asyncio.Event()
response_handler_cancelled_app.ctx.flag = False


@response_timeout_app.route("/1")
async def handler_1(request):
    await asyncio.sleep(2)
    return text("OK")


@response_ws_app.websocket("/ws")
async def ws_handler(request, ws):
    sleep(2)
    await asyncio.sleep(0)
    request.app.ctx.event.set()


@response_timeout_app.exception(ServiceUnavailable)
def handler_exception(request, exception):
    return text("Response Timeout from error_handler.", 503)


@response_timeout_default_app.route("/1")
async def handler_2(request):
    await asyncio.sleep(2)
    return text("OK")


@response_handler_cancelled_app.exception(asyncio.CancelledError)
def handler_cancelled(request, exception):
    # If we get a CancelledError, it means sanic has already sent a response,
    # we should not ever have to handle a CancelledError.
    response_handler_cancelled_app.ctx.flag = True
    return text("App received CancelledError!", 500)
    # The client will never receive this response, because the socket
    # is already closed when we get a CancelledError.


@response_handler_cancelled_app.route("/1")
async def handler_3(request):
    await asyncio.sleep(2)
    return text("OK")


def test_server_error_response_timeout():
    request, response = response_timeout_app.test_client.get("/1")
    assert response.status == 503
    assert response.text == "Response Timeout from error_handler."


def test_default_server_error_response_timeout():
    request, response = response_timeout_default_app.test_client.get("/1")
    assert response.status == 503
    assert "Response Timeout" in response.text


def test_response_handler_cancelled():
    request, response = response_handler_cancelled_app.test_client.get("/1")
    assert response.status == 503
    assert "Response Timeout" in response.text
    assert response_handler_cancelled_app.ctx.flag is False


# @pytest.mark.asyncio
def test_response_timeout_not_applied():
    _ = response_ws_app.test_client.websocket("/ws")
    assert response_ws_app.ctx.event.is_set()
