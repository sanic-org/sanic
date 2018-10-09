from sanic import Sanic
import asyncio
from sanic.response import text
from sanic.exceptions import ServiceUnavailable
from sanic.config import Config

Config.RESPONSE_TIMEOUT = 1
response_timeout_app = Sanic('test_response_timeout')
response_timeout_default_app = Sanic('test_response_timeout_default')
response_handler_cancelled_app = Sanic('test_response_handler_cancelled')


@response_timeout_app.route('/1')
async def handler_1(request):
    await asyncio.sleep(2)
    return text('OK')


@response_timeout_app.exception(ServiceUnavailable)
def handler_exception(request, exception):
    return text('Response Timeout from error_handler.', 503)


def test_server_error_response_timeout():
    request, response = response_timeout_app.test_client.get('/1')
    assert response.status == 503
    assert response.text == 'Response Timeout from error_handler.'


@response_timeout_default_app.route('/1')
async def handler_2(request):
    await asyncio.sleep(2)
    return text('OK')


def test_default_server_error_response_timeout():
    request, response = response_timeout_default_app.test_client.get('/1')
    assert response.status == 503
    assert response.text == 'Error: Response Timeout'


response_handler_cancelled_app.flag = False


@response_handler_cancelled_app.exception(asyncio.CancelledError)
def handler_cancelled(request, exception):
    # If we get a CancelledError, it means sanic has already sent a response,
    # we should not ever have to handle a CancelledError.
    response_handler_cancelled_app.flag = True
    return text("App received CancelledError!", 500)
    # The client will never receive this response, because the socket
    # is already closed when we get a CancelledError.


@response_handler_cancelled_app.route('/1')
async def handler_3(request):
    await asyncio.sleep(2)
    return text('OK')


def test_response_handler_cancelled():
    request, response = response_handler_cancelled_app.test_client.get('/1')
    assert response.status == 503
    assert response.text == 'Error: Response Timeout'
    assert response_handler_cancelled_app.flag is False
