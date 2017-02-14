import multiprocessing
import random
import signal

from sanic import Sanic
from sanic.testing import HOST, PORT


def test_multiprocessing():
    """Tests that the number of children we produce is correct"""
    # Selects a number at random so we can spot check
    num_workers = random.choice(range(2,  multiprocessing.cpu_count() * 2 + 1))
    app = Sanic('test_multiprocessing')
    process_list = set()

    def stop_on_alarm(*args):
        for process in multiprocessing.active_children():
            process_list.add(process.pid)
            process.terminate()

    signal.signal(signal.SIGALRM, stop_on_alarm)
    signal.alarm(1)
    app.run(HOST, PORT, workers=num_workers)

    assert len(process_list) == num_workers

