import asyncio

from time import monotonic as current_time
from unittest.mock import Mock

import pytest

from sanic import Sanic
from sanic.exceptions import RequestTimeout, ServiceUnavailable
from sanic.http import Stage
from sanic.server import HttpProtocol


@pytest.fixture
def app():
    return Sanic("test")


@pytest.fixture
def mock_transport():
    return Mock()


@pytest.fixture
def protocol(app, mock_transport):
    loop = asyncio.new_event_loop()
    protocol = HttpProtocol(loop=loop, app=app)
    protocol.connection_made(mock_transport)
    protocol._setup_connection()
    protocol._task = Mock(spec=asyncio.Task)
    protocol._task.cancel = Mock()
    return protocol


def test_setup(protocol: HttpProtocol):
    assert protocol._task is not None
    assert protocol._http is not None
    assert protocol._time is not None


def test_check_timeouts_no_timeout(protocol: HttpProtocol):
    protocol.keep_alive_timeout = 1
    protocol.loop.call_later = Mock()
    protocol.check_timeouts()
    protocol._task.cancel.assert_not_called()
    assert protocol._http.stage is Stage.IDLE
    assert protocol._http.exception is None
    protocol.loop.call_later.assert_called_with(
        protocol.keep_alive_timeout / 2, protocol.check_timeouts
    )


def test_check_timeouts_keep_alive_timeout(protocol: HttpProtocol):
    protocol._http.stage = Stage.IDLE
    protocol._time = 0
    protocol.check_timeouts()
    protocol._task.cancel.assert_called_once()
    assert protocol._http.exception is None


def test_check_timeouts_request_timeout(protocol: HttpProtocol):
    protocol._http.stage = Stage.REQUEST
    protocol._time = 0
    protocol.check_timeouts()
    protocol._task.cancel.assert_called_once()
    assert isinstance(protocol._http.exception, RequestTimeout)


def test_check_timeouts_response_timeout(protocol: HttpProtocol):
    protocol._http.stage = Stage.RESPONSE
    protocol._time = 0
    protocol.check_timeouts()
    protocol._task.cancel.assert_called_once()
    assert isinstance(protocol._http.exception, ServiceUnavailable)
