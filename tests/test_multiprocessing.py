import multiprocessing
import random
import signal
import pytest

from sanic.testing import HOST, PORT


@pytest.mark.skipif(
    not hasattr(signal, 'SIGALRM'),
    reason='SIGALRM is not implemented for this platform, we have to come '
    'up with another timeout strategy to test these'
)
def test_multiprocessing(app):
    """Tests that the number of children we produce is correct"""
    # Selects a number at random so we can spot check
    num_workers = random.choice(range(2, multiprocessing.cpu_count() * 2 + 1))
    process_list = set()

    def stop_on_alarm(*args):
        for process in multiprocessing.active_children():
            process_list.add(process.pid)
            process.terminate()

    signal.signal(signal.SIGALRM, stop_on_alarm)
    signal.alarm(3)
    app.run(HOST, PORT, workers=num_workers)

    assert len(process_list) == num_workers
