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
    time.sleep(1)
    yield
    worker.kill()


def test_gunicorn_worker(gunicorn_worker):
    with urllib.request.urlopen('http://localhost:1337/') as f:
        res = json.loads(f.read(100).decode())
    assert res['test']
