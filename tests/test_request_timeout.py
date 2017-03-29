import asyncio

import pytest

from sanic import Sanic
from sanic.config import Config
from sanic.exceptions import RequestTimeout
from sanic.response import text

Config.REQUEST_TIMEOUT = 1
request_timeout_app = Sanic('test_request_timeout')
request_timeout_default_app = Sanic('test_request_timeout_default')


@request_timeout_app.route('/1')
async def handler_1(request):
    await asyncio.sleep(2)
    return text('OK')


@request_timeout_app.exception(RequestTimeout)
def handler_exception(request, exception):
    return text('Request Timeout from error_handler.', 408)


@pytest.mark.skip("https://github.com/channelcat/sanic/issues/598")
def test_server_error_request_timeout():
    request, response = request_timeout_app.test_client.get('/1')
    assert response.status == 408
    assert response.text == 'Request Timeout from error_handler.'


@request_timeout_default_app.route('/1')
async def handler_2(request):
    await asyncio.sleep(2)
    return text('OK')


@pytest.mark.skip("https://github.com/channelcat/sanic/issues/598")
def test_default_server_error_request_timeout():
    request, response = request_timeout_default_app.test_client.get('/1')
    assert response.status == 408
    assert response.text == 'Error: Request Timeout'
