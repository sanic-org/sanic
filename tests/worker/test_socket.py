import socket

from pathlib import Path

import pytest

from sanic import Sanic
from sanic.compat import OS_IS_WINDOWS
from sanic.server.socket import (
    bind_socket,
    bind_unix_socket,
    close_socket,
    configure_socket,
    remove_unix_socket,
)


def test_setup_and_teardown_unix():
    socket_address = "./test.sock"
    path = Path.cwd() / socket_address
    assert not path.exists()
    bind_unix_socket(socket_address)
    assert path.exists()
    remove_unix_socket(socket_address)
    assert not path.exists()


def test_configure_socket():
    socket_address = "./test.sock"
    path = Path.cwd() / socket_address
    assert not path.exists()
    configure_socket({"unix": socket_address, "backlog": 100})
    assert path.exists()
    remove_unix_socket(socket_address)
    assert not path.exists()


def test_bind_socket_rebinds_same_port_after_close():
    first = bind_socket("127.0.0.1", 0)
    host, port = first.getsockname()[:2]
    close_socket(first)
    second = bind_socket(host, port)
    assert second.getsockname()[:2] == (host, port)
    close_socket(second)


def test_bind_socket_does_not_share_port_by_default():
    first = bind_socket("127.0.0.1", 0)
    host, port = first.getsockname()[:2]
    try:
        with pytest.raises(OSError):
            bind_socket(host, port)
    finally:
        close_socket(first)


@pytest.mark.skipif(
    OS_IS_WINDOWS or not hasattr(socket, "SO_REUSEPORT"),
    reason="SO_REUSEPORT is not available",
)
def test_bind_socket_can_share_port_when_reuse_port_enabled():
    first = bind_socket("127.0.0.1", 0, reuse_port=True)
    host, port = first.getsockname()[:2]
    try:
        second = bind_socket(host, port, reuse_port=True)
        assert second.getsockname()[:2] == (host, port)
        close_socket(second)
    finally:
        close_socket(first)


@pytest.mark.skipif(
    OS_IS_WINDOWS or not hasattr(socket, "SO_REUSEPORT"),
    reason="SO_REUSEPORT is not available",
)
def test_configure_socket_adopts_test_client_socket(app):
    """sanic-testing binds without reuse options, then reuses the same port.

    See: https://github.com/sanic-org/sanic/issues/3128
    """
    previous = Sanic.test_mode
    Sanic.test_mode = True
    adopted = None
    try:
        raw = socket.socket()
        raw.bind(("127.0.0.1", 0))
        host, port = raw.getsockname()

        adopted = configure_socket(
            {
                "sock": raw,
                "unix": None,
                "backlog": 100,
                "app": app,
            }
        )
        assert adopted is not None
        assert adopted.getsockname()[:2] == (host, port)
        other = bind_socket(host, port, reuse_port=True)
        assert other.getsockname()[:2] == (host, port)
        close_socket(other)
    finally:
        close_socket(adopted)
        Sanic.test_mode = previous
