from unittest.mock import Mock, call, patch

import pytest

from sanic.app import Sanic
from sanic.http.constants import HTTP
from sanic.server.runners import _run_server_forever, serve


@patch("sanic.server.runners._serve_http_1")
@patch("sanic.server.runners._serve_http_3")
def test_run_http_1(_serve_http_3: Mock, _serve_http_1: Mock, app: Sanic):
    serve("", 0, app)
    _serve_http_3.assert_not_called()
    _serve_http_1.assert_called_once()


@patch("sanic.server.runners._serve_http_1")
@patch("sanic.server.runners._serve_http_3")
def test_run_http_3(_serve_http_3: Mock, _serve_http_1: Mock, app: Sanic):
    serve("", 0, app, version=HTTP.VERSION_3)
    _serve_http_1.assert_not_called()
    _serve_http_3.assert_called_once()


@patch("sanic.server.runners.remove_unix_socket")
@pytest.mark.parametrize("do_cleanup", (True, False))
def test_run_server_forever(remove_unix_socket: Mock, do_cleanup: bool):
    loop = Mock()
    cleanup = Mock()
    loop.run_forever = Mock(side_effect=KeyboardInterrupt())
    before_stop = Mock()
    before_stop.return_value = Mock()
    after_stop = Mock()
    after_stop.return_value = Mock()
    unix = Mock()

    _run_server_forever(
        loop, before_stop, after_stop, cleanup if do_cleanup else None, unix
    )

    loop.run_forever.assert_called_once_with()
    loop.run_until_complete.assert_has_calls(
        [call(before_stop.return_value), call(after_stop.return_value)]
    )

    if do_cleanup:
        cleanup.assert_called_once_with()
    else:
        cleanup.assert_not_called()

    remove_unix_socket.assert_called_once_with(unix)
    loop.close.assert_called_once_with()
