import json
import os
import sys

from pathlib import Path
from typing import List, Optional, Tuple

import pytest

from sanic_routing import __version__ as __routing_version__

from sanic import __version__
from sanic.__main__ import main


@pytest.fixture(scope="module", autouse=True)
def tty():
    orig = sys.stdout.isatty
    sys.stdout.isatty = lambda: False
    yield
    sys.stdout.isatty = orig


def capture(command: List[str], caplog):
    caplog.clear()
    os.chdir(Path(__file__).parent)
    try:
        main(command)
    except SystemExit:
        ...
    return [record.message for record in caplog.records]


def read_app_info(lines: List[str]):
    for line in lines:
        if line.startswith("{") and line.endswith("}"):  # type: ignore
            return json.loads(line)


@pytest.mark.parametrize(
    "appname,extra",
    (
        ("fake.server.app", None),
        ("fake.server:create_app", "--factory"),
        ("fake.server.create_app()", None),
    ),
)
def test_server_run(
    appname: str,
    extra: Optional[str],
    caplog: pytest.LogCaptureFixture,
):
    command = [appname]
    if extra:
        command.append(extra)
    lines = capture(command, caplog)

    assert "Goin' Fast @ http://127.0.0.1:8000" in lines


def test_server_run_factory_with_args(caplog):
    command = [
        "fake.server.create_app_with_args",
        "--factory",
    ]
    lines = capture(command, caplog)

    assert "module=fake.server.create_app_with_args" in lines


def test_server_run_factory_with_args_arbitrary(caplog):
    command = [
        "fake.server.create_app_with_args",
        "--factory",
        "--foo=bar",
    ]
    lines = capture(command, caplog)

    assert "foo=bar" in lines


def test_error_with_function_as_instance_without_factory_arg(caplog):
    command = ["fake.server.create_app"]
    lines = capture(command, caplog)
    assert (
        "Failed to run app: Module is not a Sanic app, it is a function\n  "
        "If this callable returns a Sanic instance try: \n"
        "sanic fake.server.create_app --factory"
    ) in lines


def test_error_with_path_as_instance_without_simple_arg(caplog):
    command = ["./fake/"]
    lines = capture(command, caplog)
    assert (
        "Failed to run app: App not found.\n   Please use --simple if you "
        "are passing a directory to sanic.\n   eg. sanic ./fake/ --simple"
    ) in lines


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
def test_tls_options(cmd: Tuple[str, ...], caplog):
    command = ["fake.server.app", *cmd, "--port=9999", "--debug"]
    lines = capture(command, caplog)
    assert "Goin' Fast @ https://127.0.0.1:9999" in lines


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
def test_tls_wrong_options(cmd: Tuple[str, ...], caplog):
    command = ["fake.server.app", *cmd, "-p=9999", "--debug"]
    lines = capture(command, caplog)

    assert (
        "TLS certificates must be specified by either of:\n  "
        "--cert certdir/fullchain.pem --key certdir/privkey.pem\n  "
        "--tls certdir  (equivalent to the above)"
    ) in lines


@pytest.mark.parametrize(
    "cmd",
    (
        ("--host=localhost", "--port=9999"),
        ("-H", "localhost", "-p", "9999"),
    ),
)
def test_host_port_localhost(cmd: Tuple[str, ...], caplog):
    command = ["fake.server.app", *cmd]
    lines = capture(command, caplog)
    expected = "Goin' Fast @ http://localhost:9999"

    assert expected in lines


@pytest.mark.parametrize(
    "cmd,expected",
    (
        (
            ("--host=localhost", "--port=9999"),
            "Goin' Fast @ http://localhost:9999",
        ),
        (
            ("-H", "localhost", "-p", "9999"),
            "Goin' Fast @ http://localhost:9999",
        ),
        (
            ("--host=127.0.0.127", "--port=9999"),
            "Goin' Fast @ http://127.0.0.127:9999",
        ),
        (
            ("-H", "127.0.0.127", "-p", "9999"),
            "Goin' Fast @ http://127.0.0.127:9999",
        ),
        (("--host=::", "--port=9999"), "Goin' Fast @ http://[::]:9999"),
        (("-H", "::", "-p", "9999"), "Goin' Fast @ http://[::]:9999"),
        (("--host=::1", "--port=9999"), "Goin' Fast @ http://[::1]:9999"),
        (("-H", "::1", "-p", "9999"), "Goin' Fast @ http://[::1]:9999"),
    ),
)
def test_host_port(cmd: Tuple[str, ...], expected: str, caplog):
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
def test_num_workers(num: int, cmd: Tuple[str, ...], caplog):
    command = ["fake.server.app", *cmd]
    lines = capture(command, caplog)

    if num == 1:
        expected = "mode: production, single worker"
    else:
        expected = f"mode: production, w/ {num} workers"

    assert expected in lines


@pytest.mark.parametrize("cmd", ("--debug",))
def test_debug(cmd: str, caplog):
    command = ["fake.server.app", cmd]
    lines = capture(command, caplog)
    info = read_app_info(lines)

    assert info["debug"] is True
    assert info["auto_reload"] is False


@pytest.mark.parametrize("cmd", ("--dev", "-d"))
def test_dev(cmd: str, caplog):
    command = ["fake.server.app", cmd]
    lines = capture(command, caplog)
    info = read_app_info(lines)

    assert info["debug"] is True
    assert info["auto_reload"] is True


@pytest.mark.parametrize("cmd", ("--auto-reload", "-r"))
def test_auto_reload(cmd: str, caplog):
    command = ["fake.server.app", cmd]
    lines = capture(command, caplog)
    info = read_app_info(lines)

    assert info["debug"] is False
    assert info["auto_reload"] is True


@pytest.mark.parametrize(
    "cmd,expected",
    (
        ("", False),
        ("--debug", True),
        ("--access-log", True),
        ("--no-access-log", False),
    ),
)
def test_access_logs(cmd: str, expected: bool, caplog):
    command = ["fake.server.app"]
    if cmd:
        command.append(cmd)
    lines = capture(command, caplog)
    info = read_app_info(lines)

    assert info["access_log"] is expected


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
def test_noisy_exceptions(cmd: str, expected: bool, caplog):
    command = ["fake.server.app", cmd]
    lines = capture(command, caplog)
    info = read_app_info(lines)

    assert info["noisy_exceptions"] is expected
