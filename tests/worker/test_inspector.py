import json

from datetime import datetime
from logging import ERROR, INFO
from socket import AF_INET, SOCK_STREAM, timeout
from unittest.mock import Mock, patch

import pytest

from sanic.log import Colors
from sanic.worker.inspector import Inspector, inspect


DATA = {
    "info": {
        "packages": ["foo"],
    },
    "extra": {
        "more": "data",
    },
    "workers": {"Worker-Name": {"some": "state"}},
}
SERIALIZED = json.dumps(DATA)


def test_inspector_stop():
    inspector = Inspector(Mock(), {}, {}, "", 1)
    assert inspector.run is True
    inspector.stop()
    assert inspector.run is False


@patch("sanic.worker.inspector.sys.stdout.write")
@patch("sanic.worker.inspector.socket")
@pytest.mark.parametrize("command", ("foo", "raw", "pretty"))
def test_send_inspect(socket: Mock, write: Mock, command: str):
    socket.return_value = socket
    socket.__enter__.return_value = socket
    socket.recv.return_value = SERIALIZED.encode()
    inspect("localhost", 9999, command)

    socket.sendall.assert_called_once_with(command.encode())
    socket.recv.assert_called_once_with(4096)
    socket.connect.assert_called_once_with(("localhost", 9999))
    socket.assert_called_once_with(AF_INET, SOCK_STREAM)

    if command == "raw":
        write.assert_called_once_with(SERIALIZED)
    elif command == "pretty":
        write.assert_called()
    else:
        write.assert_not_called()


@patch("sanic.worker.inspector.sys")
@patch("sanic.worker.inspector.socket")
def test_send_inspect_conn_refused(socket: Mock, sys: Mock, caplog):
    with caplog.at_level(INFO):
        socket.return_value = socket
        socket.__enter__.return_value = socket
        socket.connect.side_effect = ConnectionRefusedError()
        inspect("localhost", 9999, "foo")

        socket.close.assert_called_once()
        sys.exit.assert_called_once_with(1)

    message = (
        f"{Colors.RED}Could not connect to inspector at: "
        f"{Colors.YELLOW}('localhost', 9999){Colors.END}\n"
        "Either the application is not running, or it did not start "
        "an inspector instance."
    )
    assert ("sanic.error", ERROR, message) in caplog.record_tuples


@patch("sanic.worker.inspector.configure_socket")
@pytest.mark.parametrize("action", (b"reload", b"shutdown", b"foo"))
def test_run_inspector(configure_socket: Mock, action: bytes):
    sock = Mock()
    conn = Mock()
    conn.recv.return_value = action
    configure_socket.return_value = sock
    inspector = Inspector(Mock(), {}, {}, "localhost", 9999)
    inspector.reload = Mock()  # type: ignore
    inspector.shutdown = Mock()  # type: ignore
    inspector.state_to_json = Mock(return_value="foo")  # type: ignore

    def accept():
        inspector.run = False
        return conn, ...

    sock.accept = accept

    inspector()

    configure_socket.assert_called_once_with(
        {"host": "localhost", "port": 9999, "unix": None, "backlog": 1}
    )
    conn.recv.assert_called_with(64)

    if action == b"reload":
        conn.send.assert_called_with(b"\n")
        inspector.reload.assert_called()
        inspector.shutdown.assert_not_called()
        inspector.state_to_json.assert_not_called()
    elif action == b"shutdown":
        conn.send.assert_called_with(b"\n")
        inspector.reload.assert_not_called()
        inspector.shutdown.assert_called()
        inspector.state_to_json.assert_not_called()
    else:
        conn.send.assert_called_with(b'"foo"')
        inspector.reload.assert_not_called()
        inspector.shutdown.assert_not_called()
        inspector.state_to_json.assert_called()


@patch("sanic.worker.inspector.configure_socket")
def test_accept_timeout(configure_socket: Mock):
    sock = Mock()
    configure_socket.return_value = sock
    inspector = Inspector(Mock(), {}, {}, "localhost", 9999)
    inspector.reload = Mock()  # type: ignore
    inspector.shutdown = Mock()  # type: ignore
    inspector.state_to_json = Mock(return_value="foo")  # type: ignore

    def accept():
        inspector.run = False
        raise timeout

    sock.accept = accept

    inspector()

    inspector.reload.assert_not_called()
    inspector.shutdown.assert_not_called()
    inspector.state_to_json.assert_not_called()


def test_state_to_json():
    now = datetime.now()
    now_iso = now.isoformat()
    app_info = {"app": "hello"}
    worker_state = {"Test": {"now": now, "nested": {"foo": now}}}
    inspector = Inspector(Mock(), app_info, worker_state, "", 0)
    state = inspector.state_to_json()

    assert state == {
        "info": app_info,
        "workers": {"Test": {"now": now_iso, "nested": {"foo": now_iso}}},
    }


def test_reload():
    publisher = Mock()
    inspector = Inspector(publisher, {}, {}, "", 0)
    inspector.reload()

    publisher.send.assert_called_once_with("__ALL_PROCESSES__:")


def test_shutdown():
    publisher = Mock()
    inspector = Inspector(publisher, {}, {}, "", 0)
    inspector.shutdown()

    publisher.send.assert_called_once_with("__TERMINATE__")
