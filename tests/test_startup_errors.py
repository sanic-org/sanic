import errno

import pytest

from sanic.exceptions import ServerError
from sanic.startup.errors import (
    _handle_os_error,
    _handle_server_error,
    maybe_handle_startup_error,
)


def test_handle_os_error_address_in_use(caplog):
    exc = OSError(errno.EADDRINUSE, "Address already in use")
    result = _handle_os_error(exc)

    assert result is True
    assert "address already in use" in caplog.text.lower()
    assert "Ensure no other process" in caplog.text


def test_handle_os_error_other_errno(caplog):
    exc = OSError(13, "Permission denied")
    exc.strerror = "Permission denied"
    result = _handle_os_error(exc)

    assert result is True
    assert "Permission denied" in caplog.text
    assert "errno 13" in caplog.text


def test_handle_os_error_non_os_error():
    exc = ValueError("not an OS error")
    result = _handle_os_error(exc)

    assert result is False


def test_handle_server_error(caplog):
    exc = ServerError("Something went wrong")
    result = _handle_server_error(exc)

    assert result is True
    assert "Startup failed due to server error" in caplog.text
    assert "Something went wrong" in caplog.text


def test_handle_server_error_non_server_error():
    exc = ValueError("not a server error")
    result = _handle_server_error(exc)

    assert result is False


def test_maybe_handle_startup_error_exits_on_os_error():
    exc = OSError(errno.EADDRINUSE, "Address already in use")
    with pytest.raises(SystemExit) as exc_info:
        maybe_handle_startup_error(exc)

    assert exc_info.value.code == 1


def test_maybe_handle_startup_error_exits_on_server_error():
    exc = ServerError("test error")
    with pytest.raises(SystemExit) as exc_info:
        maybe_handle_startup_error(exc)

    assert exc_info.value.code == 1


def test_maybe_handle_startup_error_raises_unhandled():
    exc = ValueError("unhandled error")
    with pytest.raises(ValueError, match="unhandled error"):
        maybe_handle_startup_error(exc)


def test_maybe_handle_startup_error_raises_runtime_error():
    exc = RuntimeError("some runtime error")
    with pytest.raises(RuntimeError, match="some runtime error"):
        maybe_handle_startup_error(exc)
