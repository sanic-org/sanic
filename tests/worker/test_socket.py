from pathlib import Path
from unittest.mock import Mock, patch

from sanic.server.socket import (
    bind_socket,
    bind_unix_socket,
    configure_socket,
    remove_unix_socket,
)


def test_bind_socket_does_not_reuse_address_on_windows():
    sock = Mock()
    with (
        patch("sanic.server.socket.OS_IS_WINDOWS", True),
        patch("sanic.server.socket.socket.socket", return_value=sock),
    ):
        bind_socket("127.0.0.1", 8000)

    sock.setsockopt.assert_not_called()
    sock.bind.assert_called_once_with(("127.0.0.1", 8000))


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
