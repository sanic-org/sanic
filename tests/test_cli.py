import json
import os
import sys

from pathlib import Path
from typing import List, Optional, Tuple
from unittest.mock import patch

import pytest

from sanic_routing import __version__ as __routing_version__

from sanic import __version__
from sanic.__main__ import main
from sanic.cli.inspector_client import InspectorClient

from .conftest import get_port


@pytest.fixture(scope="module", autouse=True)
def tty():
    orig = sys.stdout.isatty
    sys.stdout.isatty = lambda: False
    yield
    sys.stdout.isatty = orig


def capture(command: List[str], caplog=None, capsys=None):
    if capsys:
        capsys.readouterr()
    if caplog:
        caplog.clear()
    os.chdir(Path(__file__).parent)
    try:
        main(command)
    except SystemExit:
        ...
    if capsys:
        captured_err = capsys.readouterr()
        return captured_err
    if caplog:
        return [record.message for record in caplog.records]
    return None


def read_app_info(lines: List[str]):
    for line in lines:
        if line.startswith("{") and line.endswith("}"):  # type: ignore
            return json.loads(line)


@pytest.mark.parametrize(
    "appname,extra",
    (
        ("fake.server.app", None),
        ("fake.server", None),
        ("fake.server:create_app", "--factory"),
        ("fake.server.create_app()", None),
        ("fake.server.create_app", None),
    ),
)
def test_server_run(
    appname: str, extra: Optional[str], caplog: pytest.LogCaptureFixture, port
):
    command = [appname, f"-p={port}"]
    if extra:
        command.append(extra)
    lines = capture(command, caplog)

    assert f"Goin' Fast @ http://127.0.0.1:{port}" in lines


@pytest.mark.parametrize(
    "command",
    (
        ["fake.server.create_app_with_args", "--factory"],
        ["fake.server.create_app_with_args"],
    ),
)
def test_server_run_factory_with_args(caplog, command, port):
    command.append(f"-p={port}")
    lines = capture(command, caplog)

    assert "target=fake.server.create_app_with_args" in lines


def test_server_run_factory_with_args_arbitrary(caplog, port):
    command = [
        "fake.server.create_app_with_args",
        "--factory",
        "--foo=bar",
        f"-p={port}",
    ]
    lines = capture(command, caplog)

    assert "foo=bar" in lines


@pytest.mark.parametrize(
    "cmd",
    (
        (
            "--cert=certs/sanic.example/fullchain.pem",
            "--key=certs/sanic.example/privkey.pem",
        ),
        (
            "--tls=certs/sanic.example/",
            "--tls=certs/localhost/",
        ),
        (
            "--tls=certs/sanic.example/",
            "--tls=certs/localhost/",
            "--tls-strict-host",
        ),
    ),
)
def test_tls_options(cmd: Tuple[str, ...], caplog, port):
    command = [
        "fake.server.app",
        *cmd,
        f"--port={port}",
        "--debug",
        "--single-process",
    ]
    lines = capture(command, caplog)
    assert f"Goin' Fast @ https://127.0.0.1:{port}" in lines


@pytest.mark.parametrize(
    "cmd",
    (
        ("--cert=certs/sanic.example/fullchain.pem",),
        (
            "--cert=certs/sanic.example/fullchain.pem",
            "--key=certs/sanic.example/privkey.pem",
            "--tls=certs/localhost/",
        ),
        ("--tls-strict-host",),
    ),
)
def test_tls_wrong_options(cmd: Tuple[str, ...], caplog, port):
    command = ["fake.server.app", *cmd, f"-p={port}", "--debug"]
    lines = capture(command, caplog)

    assert (
        "TLS certificates must be specified by either of:\n  "
        "--cert certdir/fullchain.pem --key certdir/privkey.pem\n  "
        "--tls certdir  (equivalent to the above)"
    ) in lines


@pytest.mark.parametrize(
    "cmd",
    (
        ("--host=localhost", "--port={port}"),
        ("-H", "localhost", "-p", "{port}"),
    ),
)
def test_host_port_localhost(cmd: Tuple[str, ...], caplog, port):
    cmd = [c.format(port=str(port)) for c in cmd]
    command = ["fake.server.app", *cmd]
    lines = capture(command, caplog)
    expected = f"Goin' Fast @ http://localhost:{port}"

    assert expected in lines


@pytest.mark.parametrize(
    "cmd,expected",
    (
        (
            ("--host=localhost", "--port={port}"),
            "Goin' Fast @ http://localhost:{port}",
        ),
        (
            ("-H", "localhost", "-p", "{port}"),
            "Goin' Fast @ http://localhost:{port}",
        ),
        (
            ("--host=127.0.0.1", "--port={port}"),
            "Goin' Fast @ http://127.0.0.1:{port}",
        ),
        (
            ("-H", "127.0.0.1", "-p", "{port}"),
            "Goin' Fast @ http://127.0.0.1:{port}",
        ),
        (("--host=::", "--port={port}"), "Goin' Fast @ http://[::]:{port}"),
        (("-H", "::", "-p", "{port}"), "Goin' Fast @ http://[::]:{port}"),
        (("--host=::1", "--port={port}"), "Goin' Fast @ http://[::1]:{port}"),
        (("-H", "::1", "-p", "{port}"), "Goin' Fast @ http://[::1]:{port}"),
    ),
)
def test_host_port(cmd: Tuple[str, ...], expected: str, caplog, port):
    cmd = [c.format(port=str(port)) for c in cmd]
    expected = expected.format(port=str(port))
    command = ["fake.server.app", *cmd]
    lines = capture(command, caplog)

    assert expected in lines


@pytest.mark.parametrize(
    "num,cmd",
    (
        (1, (f"--workers={1}",)),
        (2, (f"--workers={2}",)),
        (4, (f"--workers={4}",)),
        (1, ("-w", "1")),
        (2, ("-w", "2")),
        (4, ("-w", "4")),
    ),
)
def test_num_workers(num: int, cmd: Tuple[str, ...], caplog, port):
    command = ["fake.server.app", *cmd, f"-p={port}"]
    lines = capture(command, caplog)

    if num == 1:
        expected = "mode: production, single worker"
    else:
        expected = f"mode: production, w/ {num} workers"

    assert expected in lines


@pytest.mark.parametrize("cmd", ("--debug",))
def test_debug(cmd: str, caplog, port):
    command = ["fake.server.app", cmd, f"-p={port}"]
    lines = capture(command, caplog)
    info = read_app_info(lines)

    assert info["debug"] is True
    assert info["auto_reload"] is False


@pytest.mark.parametrize("cmd", ("--dev", "-d"))
def test_dev(cmd: str, caplog, port):
    command = ["fake.server.app", cmd, f"-p={port}"]
    lines = capture(command, caplog)
    info = read_app_info(lines)

    assert info["debug"] is True
    assert info["auto_reload"] is True


@pytest.mark.parametrize("cmd", ("--auto-reload", "-r"))
def test_auto_reload(cmd: str, caplog, port):
    command = ["fake.server.app", cmd, f"-p={port}"]
    lines = capture(command, caplog)
    info = read_app_info(lines)

    assert info["debug"] is False, f"Unexpected value of debug {info}"
    assert (
        info["auto_reload"] is True
    ), f"Unexpected value of auto reload {info}"


@pytest.mark.parametrize(
    "cmd,expected",
    (
        ("", False),
        ("--debug", True),
        ("--access-log", True),
        ("--no-access-log", False),
    ),
)
def test_access_logs(cmd: str, expected: bool, caplog, port):
    command = ["fake.server.app", f"-p={port}"]
    if cmd:
        command.append(cmd)
    lines = capture(command, caplog)
    print(lines)
    info = read_app_info(lines)
    if info["access_log"] != expected:
        print(lines)
    assert (
        info["access_log"] is expected
    ), f"Expected: {expected}. Received: {info}. Lines: {lines}"


@pytest.mark.parametrize("cmd", ("--version", "-v"))
def test_version(cmd: str, caplog, capsys):
    command = [cmd]
    capture(command, caplog)
    version_string = f"Sanic {__version__}; Routing {__routing_version__}\n"
    out, _ = capsys.readouterr()
    assert version_string == out


@pytest.mark.parametrize(
    "cmd,expected",
    (
        ("--noisy-exceptions", True),
        ("--no-noisy-exceptions", False),
    ),
)
def test_noisy_exceptions(cmd: str, expected: bool, caplog, port):
    command = ["fake.server.app", cmd, f"-p={port}"]
    lines = capture(command, caplog)
    info = read_app_info(lines)

    assert info["noisy_exceptions"] is expected


def test_inspector_inspect(urlopen, caplog, capsys):
    urlopen.read.return_value = json.dumps(
        {
            "result": {
                "info": {
                    "packages": ["foo"],
                },
                "extra": {
                    "more": "data",
                },
                "workers": {"Worker-Name": {"some": "state"}},
            }
        }
    ).encode()
    with patch("sys.argv", ["sanic", "inspect"]):
        capture(["inspect"], caplog)
    captured = capsys.readouterr()
    assert "Inspecting @ http://localhost:6457" in captured.out
    assert "Worker-Name" in captured.out
    assert captured.err == ""


@pytest.mark.parametrize(
    "command,params",
    (
        (["reload"], {"zero_downtime": False}),
        (["reload", "--zero-downtime"], {"zero_downtime": True}),
        (["shutdown"], {}),
        (["scale", "9"], {"replicas": 9}),
        (["foo", "--bar=something"], {"bar": "something"}),
        (["foo", "--bar"], {"bar": True}),
        (["foo", "--no-bar"], {"bar": False}),
        (["foo", "positional"], {"args": ["positional"]}),
        (
            ["foo", "positional", "--bar=something"],
            {"args": ["positional"], "bar": "something"},
        ),
    ),
)
def test_inspector_command(command, params):
    with patch.object(InspectorClient, "request") as client:
        with patch("sys.argv", ["sanic", "inspect", *command]):
            main()

    client.assert_called_once_with(command[0], **params)


def test_server_run_with_repl(caplog, capsys):
    record = (
        "sanic.error",
        40,
        "Can't start REPL in non-interactive mode. "
        "You can only run with --repl in a TTY.",
    )

    def run():
        command = ["fake.server.app", "--repl", f"-p={get_port()}"]
        return capture(command, capsys=capsys)

    with patch("sanic.cli.app.is_atty", return_value=True):
        result = run()

    assert record not in caplog.record_tuples
    assert "Welcome to the Sanic interactive console" in result.err
    assert ">>> " in result.out

    run()
    assert record in caplog.record_tuples
