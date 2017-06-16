import time
import json
import shlex
import subprocess
import urllib.request

import pytest


@pytest.fixture(scope='module')
def gunicorn_worker():
    command = 'gunicorn --bind 127.0.0.1:1337 --worker-class sanic.worker.GunicornWorker examples.simple_server:app'
    worker = subprocess.Popen(shlex.split(command))
    time.sleep(3)
    yield
    worker.kill()


def test_gunicorn_worker(gunicorn_worker):
    with urllib.request.urlopen('http://localhost:1337/') as f:
        res = json.loads(f.read(100).decode())
    assert res['test']


#########################################################
from unittest import mock
from sanic.worker import GunicornWorker
from sanic.app import Sanic
import asyncio
import logging
from aiohttp.test_utils import make_mocked_coro


class GunicornTestWorker(GunicornWorker):

    def __init__(self):
        self.app = mock.Mock()
        self.app.callable = Sanic("test_gunicorn_worker")
        self.servers = {}
        self.exit_code = 0
        self.cfg = mock.Mock()


@pytest.fixture
def worker():
    return GunicornTestWorker()


@pytest.fixture
def loop():
    return asyncio.get_event_loop()


def test_worker_init_process(worker):
    with mock.patch('sanic.worker.asyncio') as mock_asyncio:
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
    with mock.patch('sanic.worker.sys') as mock_sys:
        worker.handle_abort(object(), object())
        assert not worker.alive
        assert worker.exit_code == 1
        mock_sys.exit.assert_called_with(1)


def test_handle_quit(worker):
    worker.handle_quit(object(), object())
    assert not worker.alive
    assert worker.exit_code == 0

