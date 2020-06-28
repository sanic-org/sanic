import asyncio
import json
import shlex
import subprocess
import time
import urllib.request

from unittest import mock

import pytest

from sanic.app import Sanic
from sanic.worker import GunicornWorker


@pytest.fixture(scope="module")
def gunicorn_worker():
    command = (
        "gunicorn "
        "--bind 127.0.0.1:1337 "
        "--worker-class sanic.worker.GunicornWorker "
        "examples.simple_server:app"
    )
    worker = subprocess.Popen(shlex.split(command))
    time.sleep(3)
    yield
    worker.kill()


@pytest.fixture(scope="module")
def gunicorn_worker_with_access_logs():
    command = (
        "gunicorn "
        "--bind 127.0.0.1:1338 "
        "--worker-class sanic.worker.GunicornWorker "
        "examples.simple_server:app"
    )
    worker = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
    time.sleep(2)
    return worker


@pytest.fixture(scope="module")
def gunicorn_worker_with_env_var():
    command = (
        'env SANIC_ACCESS_LOG="False" '
        "gunicorn "
        "--bind 127.0.0.1:1339 "
        "--worker-class sanic.worker.GunicornWorker "
        "--log-level info "
        "examples.simple_server:app"
    )
    worker = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
    time.sleep(2)
    return worker


def test_gunicorn_worker(gunicorn_worker):
    with urllib.request.urlopen("http://localhost:1337/") as f:
        res = json.loads(f.read(100).decode())
    assert res["test"]


def test_gunicorn_worker_no_logs(gunicorn_worker_with_env_var):
    """
    if SANIC_ACCESS_LOG was set to False do not show access logs
    """
    with urllib.request.urlopen("http://localhost:1339/") as _:
        gunicorn_worker_with_env_var.kill()
        assert not gunicorn_worker_with_env_var.stdout.read()


def test_gunicorn_worker_with_logs(gunicorn_worker_with_access_logs):
    """
    default - show access logs
    """
    with urllib.request.urlopen("http://localhost:1338/") as _:
        gunicorn_worker_with_access_logs.kill()
        assert (
            b"(sanic.access)[INFO][127.0.0.1"
            in gunicorn_worker_with_access_logs.stdout.read()
        )


class GunicornTestWorker(GunicornWorker):
    def __init__(self):
        self.app = mock.Mock()
        self.app.callable = Sanic("test_gunicorn_worker")
        self.servers = {}
        self.exit_code = 0
        self.cfg = mock.Mock()
        self.notify = mock.Mock()


@pytest.fixture
def worker():
    return GunicornTestWorker()


def test_worker_init_process(worker):
    with mock.patch("sanic.worker.asyncio") as mock_asyncio:
        try:
            worker.init_process()
        except TypeError:
            pass

        assert mock_asyncio.get_event_loop.return_value.close.called
        assert mock_asyncio.new_event_loop.called
        assert mock_asyncio.set_event_loop.called


def test_worker_init_signals(worker):
    worker.loop = mock.Mock()
    worker.init_signals()
    assert worker.loop.add_signal_handler.called


def test_handle_abort(worker):
    with mock.patch("sanic.worker.sys") as mock_sys:
        worker.handle_abort(object(), object())
        assert not worker.alive
        assert worker.exit_code == 1
        mock_sys.exit.assert_called_with(1)


def test_handle_quit(worker):
    worker.handle_quit(object(), object())
    assert not worker.alive
    assert worker.exit_code == 0


async def _a_noop(*a, **kw):
    pass


def test_run_max_requests_exceeded(worker):
    loop = asyncio.new_event_loop()
    worker.ppid = 1
    worker.alive = True
    sock = mock.Mock()
    sock.cfg_addr = ("localhost", 8080)
    worker.sockets = [sock]
    worker.wsgi = mock.Mock()
    worker.connections = set()
    worker.log = mock.Mock()
    worker.loop = loop
    worker.servers = {
        "server1": {"requests_count": 14},
        "server2": {"requests_count": 15},
    }
    worker.max_requests = 10
    worker._run = mock.Mock(wraps=_a_noop)

    # exceeding request count
    _runner = asyncio.ensure_future(worker._check_alive(), loop=loop)
    loop.run_until_complete(_runner)

    assert not worker.alive
    worker.notify.assert_called_with()
    worker.log.info.assert_called_with(
        "Max requests exceeded, shutting " "down: %s", worker
    )


def test_worker_close(worker):
    loop = asyncio.new_event_loop()
    asyncio.sleep = mock.Mock(wraps=_a_noop)
    worker.ppid = 1
    worker.pid = 2
    worker.cfg.graceful_timeout = 1.0
    worker.signal = mock.Mock()
    worker.signal.stopped = False
    worker.wsgi = mock.Mock()
    conn = mock.Mock()
    conn.websocket = mock.Mock()
    conn.websocket.close_connection = mock.Mock(wraps=_a_noop)
    worker.connections = set([conn])
    worker.log = mock.Mock()
    worker.loop = loop
    server = mock.Mock()
    server.close = mock.Mock(wraps=lambda *a, **kw: None)
    server.wait_closed = mock.Mock(wraps=_a_noop)
    worker.servers = {server: {"requests_count": 14}}
    worker.max_requests = 10

    # close worker
    _close = asyncio.ensure_future(worker.close(), loop=loop)
    loop.run_until_complete(_close)

    assert worker.signal.stopped
    assert conn.websocket.close_connection.called
    assert len(worker.servers) == 0
