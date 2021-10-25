import json
import subprocess

from pathlib import Path

import pytest

from sanic_routing import __version__ as __routing_version__

from sanic import __version__
from sanic.config import BASE_LOGO


def capture(command):
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=Path(__file__).parent,
    )
    try:
        out, err = proc.communicate(timeout=0.5)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
    return out, err, proc.returncode


@pytest.mark.parametrize(
    "appname",
    (
        "fake.server.app",
        "fake.server:app",
        "fake.server:create_app()",
        "fake.server.create_app()",
    ),
)
def test_server_run(appname):
    command = ["sanic", appname]
    out, err, exitcode = capture(command)
    lines = out.split(b"\n")
    firstline = lines[6]

    assert exitcode != 1
    assert firstline == b"Goin' Fast @ http://127.0.0.1:8000"


@pytest.mark.parametrize(
    "cmd",
    (
        ("--host=localhost", "--port=9999"),
        ("-H", "localhost", "-p", "9999"),
    ),
)
def test_host_port_localhost(cmd):
    command = ["sanic", "fake.server.app", *cmd]
    out, err, exitcode = capture(command)
    lines = out.split(b"\n")
    firstline = lines[6]

    assert exitcode != 1
    assert firstline == b"Goin' Fast @ http://localhost:9999"


@pytest.mark.parametrize(
    "cmd",
    (
        ("--host=127.0.0.127", "--port=9999"),
        ("-H", "127.0.0.127", "-p", "9999"),
    ),
)
def test_host_port_ipv4(cmd):
    command = ["sanic", "fake.server.app", *cmd]
    out, err, exitcode = capture(command)
    lines = out.split(b"\n")
    firstline = lines[6]

    assert exitcode != 1
    assert firstline == b"Goin' Fast @ http://127.0.0.127:9999"


@pytest.mark.parametrize(
    "cmd",
    (
        ("--host=::", "--port=9999"),
        ("-H", "::", "-p", "9999"),
    ),
)
def test_host_port_ipv6_any(cmd):
    command = ["sanic", "fake.server.app", *cmd]
    out, err, exitcode = capture(command)
    lines = out.split(b"\n")
    firstline = lines[6]

    assert exitcode != 1
    assert firstline == b"Goin' Fast @ http://[::]:9999"


@pytest.mark.parametrize(
    "cmd",
    (
        ("--host=::1", "--port=9999"),
        ("-H", "::1", "-p", "9999"),
    ),
)
def test_host_port_ipv6_loopback(cmd):
    command = ["sanic", "fake.server.app", *cmd]
    out, err, exitcode = capture(command)
    lines = out.split(b"\n")
    firstline = lines[6]

    assert exitcode != 1
    assert firstline == b"Goin' Fast @ http://[::1]:9999"


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
def test_num_workers(num, cmd):
    command = ["sanic", "fake.server.app", *cmd]
    out, err, exitcode = capture(command)
    lines = out.split(b"\n")

    worker_lines = [line for line in lines if b"worker" in line]
    assert exitcode != 1
    assert len(worker_lines) == num * 2


@pytest.mark.parametrize("cmd", ("--debug", "-d"))
def test_debug(cmd):
    command = ["sanic", "fake.server.app", cmd]
    out, err, exitcode = capture(command)
    lines = out.split(b"\n")

    app_info = lines[26]
    info = json.loads(app_info)

    assert (b"\n".join(lines[:6])).decode("utf-8") == BASE_LOGO
    assert info["debug"] is True
    assert info["auto_reload"] is True


@pytest.mark.parametrize("cmd", ("--auto-reload", "-r"))
def test_auto_reload(cmd):
    command = ["sanic", "fake.server.app", cmd]
    out, err, exitcode = capture(command)
    lines = out.split(b"\n")

    app_info = lines[26]
    info = json.loads(app_info)

    assert info["debug"] is False
    assert info["auto_reload"] is True


@pytest.mark.parametrize(
    "cmd,expected", (("--access-log", True), ("--no-access-log", False))
)
def test_access_logs(cmd, expected):
    command = ["sanic", "fake.server.app", cmd]
    out, err, exitcode = capture(command)
    lines = out.split(b"\n")

    app_info = lines[26]
    info = json.loads(app_info)

    assert info["access_log"] is expected


@pytest.mark.parametrize("cmd", ("--version", "-v"))
def test_version(cmd):
    command = ["sanic", cmd]
    out, err, exitcode = capture(command)
    version_string = f"Sanic {__version__}; Routing {__routing_version__}\n"

    assert out == version_string.encode("utf-8")


@pytest.mark.parametrize(
    "cmd,expected",
    (
        ("", False),
        ("--noisy-exceptions", True),
        ("--no-noisy-exceptions", False),
    ),
)
def test_noisy_exceptions(cmd, expected):
    command = ["sanic", "fake.server.app", cmd]
    out, err, exitcode = capture(command)
    lines = out.split(b"\n")

    app_info = lines[26]
    info = json.loads(app_info)

    assert info["noisy_exceptions"] is expected
