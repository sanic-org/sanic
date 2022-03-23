import json
import subprocess

from pathlib import Path

import pytest

from sanic_routing import __version__ as __routing_version__

from sanic import __version__


def capture(command):
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=Path(__file__).parent,
    )
    try:
        out, err = proc.communicate(timeout=1)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
    return out, err, proc.returncode


def starting_line(lines):
    for idx, line in enumerate(lines):
        if line.strip().startswith(b"Sanic v"):
            return idx
    return 0


def read_app_info(lines):
    for line in lines:
        if line.startswith(b"{") and line.endswith(b"}"):
            return json.loads(line)


@pytest.mark.parametrize(
    "appname,extra",
    (
        ("fake.server.app", None),
        ("fake.server:create_app", "--factory"),
        ("fake.server.create_app()", None),
    ),
)
def test_server_run(appname, extra):
    command = ["sanic", appname]
    if extra:
        command.append(extra)
    out, err, exitcode = capture(command)
    lines = out.split(b"\n")
    firstline = lines[starting_line(lines) + 1]

    assert exitcode != 1
    assert firstline == b"Goin' Fast @ http://127.0.0.1:8000"


def test_server_run_factory_with_args():
    command = [
        "sanic",
        "fake.server.create_app_with_args",
        "--factory",
    ]
    out, err, exitcode = capture(command)
    lines = out.split(b"\n")

    assert exitcode != 1, lines
    assert b"module=fake.server.create_app_with_args" in lines


def test_server_run_factory_with_args_arbitrary():
    command = [
        "sanic",
        "fake.server.create_app_with_args",
        "--factory",
        "--foo=bar",
    ]
    out, err, exitcode = capture(command)
    lines = out.split(b"\n")

    assert exitcode != 1, lines
    assert b"foo=bar" in lines


def test_error_with_function_as_instance_without_factory_arg():
    command = ["sanic", "fake.server.create_app"]
    out, err, exitcode = capture(command)
    assert b"try: \nsanic fake.server.create_app --factory" in err
    assert exitcode != 1


def test_error_with_path_as_instance_without_simple_arg():
    command = ["sanic", "./fake/"]
    out, err, exitcode = capture(command)
    assert (
        b"Please use --simple if you are passing a directory to sanic." in err
    )
    assert exitcode != 1


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
def test_tls_options(cmd):
    command = ["sanic", "fake.server.app", *cmd, "-p=9999", "--debug"]
    out, err, exitcode = capture(command)
    assert exitcode != 1
    lines = out.split(b"\n")
    firstline = lines[starting_line(lines) + 1]
    assert firstline == b"Goin' Fast @ https://127.0.0.1:9999"


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
def test_tls_wrong_options(cmd):
    command = ["sanic", "fake.server.app", *cmd, "-p=9999", "--debug"]
    out, err, exitcode = capture(command)
    assert exitcode == 1
    assert not out
    lines = err.decode().split("\n")

    errmsg = lines[6]
    assert errmsg == "TLS certificates must be specified by either of:"


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
    expected = b"Goin' Fast @ http://localhost:9999"

    assert exitcode != 1
    assert expected in lines, f"Lines found: {lines}\nErr output: {err}"


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
    expected = b"Goin' Fast @ http://127.0.0.127:9999"

    assert exitcode != 1
    assert expected in lines, f"Lines found: {lines}\nErr output: {err}"


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
    expected = b"Goin' Fast @ http://[::]:9999"

    assert exitcode != 1
    assert expected in lines, f"Lines found: {lines}\nErr output: {err}"


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
    expected = b"Goin' Fast @ http://[::1]:9999"

    assert exitcode != 1
    assert expected in lines, f"Lines found: {lines}\nErr output: {err}"


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

    if num == 1:
        expected = b"mode: production, single worker"
    else:
        expected = (f"mode: production, w/ {num} workers").encode()

    assert exitcode != 1
    assert expected in lines, f"Expected {expected}\nLines found: {lines}"


@pytest.mark.parametrize("cmd", ("--debug",))
def test_debug(cmd):
    command = ["sanic", "fake.server.app", cmd]
    out, err, exitcode = capture(command)
    lines = out.split(b"\n")
    info = read_app_info(lines)

    assert info["debug"] is True, f"Lines found: {lines}\nErr output: {err}"
    assert (
        info["auto_reload"] is False
    ), f"Lines found: {lines}\nErr output: {err}"
    assert "dev" not in info, f"Lines found: {lines}\nErr output: {err}"


@pytest.mark.parametrize("cmd", ("--dev", "-d"))
def test_dev(cmd):
    command = ["sanic", "fake.server.app", cmd]
    out, err, exitcode = capture(command)
    lines = out.split(b"\n")
    info = read_app_info(lines)

    assert info["debug"] is True, f"Lines found: {lines}\nErr output: {err}"
    assert (
        info["auto_reload"] is True
    ), f"Lines found: {lines}\nErr output: {err}"


@pytest.mark.parametrize("cmd", ("--auto-reload", "-r"))
def test_auto_reload(cmd):
    command = ["sanic", "fake.server.app", cmd]
    out, err, exitcode = capture(command)
    lines = out.split(b"\n")
    info = read_app_info(lines)

    assert info["debug"] is False, f"Lines found: {lines}\nErr output: {err}"
    assert (
        info["auto_reload"] is True
    ), f"Lines found: {lines}\nErr output: {err}"
    assert "dev" not in info, f"Lines found: {lines}\nErr output: {err}"


@pytest.mark.parametrize(
    "cmd,expected", (("--access-log", True), ("--no-access-log", False))
)
def test_access_logs(cmd, expected):
    command = ["sanic", "fake.server.app", cmd]
    out, err, exitcode = capture(command)
    lines = out.split(b"\n")
    info = read_app_info(lines)

    assert (
        info["access_log"] is expected
    ), f"Lines found: {lines}\nErr output: {err}"


@pytest.mark.parametrize("cmd", ("--version", "-v"))
def test_version(cmd):
    command = ["sanic", cmd]
    out, err, exitcode = capture(command)
    version_string = f"Sanic {__version__}; Routing {__routing_version__}\n"

    assert out == version_string.encode("utf-8")


@pytest.mark.parametrize(
    "cmd,expected",
    (
        ("--noisy-exceptions", True),
        ("--no-noisy-exceptions", False),
    ),
)
def test_noisy_exceptions(cmd, expected):
    command = ["sanic", "fake.server.app", cmd]
    out, err, exitcode = capture(command)
    lines = out.split(b"\n")
    info = read_app_info(lines)

    assert (
        info["noisy_exceptions"] is expected
    ), f"Lines found: {lines}\nErr output: {err}"
