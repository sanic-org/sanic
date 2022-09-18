from pathlib import Path

from sanic.server.socket import (
    bind_unix_socket,
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
