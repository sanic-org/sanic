import multiprocessing
import os
import signal

import pytest

from sanic import Sanic
from sanic.utils import HOST, PORT


@pytest.mark.parametrize(
    'num_workers', list(range(2,  multiprocessing.cpu_count() * 2 + 1)))
def test_multiprocessing(num_workers):
    app = Sanic('test_json')
    process_list = multiprocessing.Manager().list()

    async def after_start(app, loop):
        process_list.append(os.getpid())
        os.kill(os.getpid(), signal.SIGTERM)

    app.run(HOST, PORT, workers=num_workers, after_start=after_start)

    assert len(process_list) == num_workers

