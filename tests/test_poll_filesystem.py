import threading
import time
import os

from sanic.reloader_helpers import poll_filesystem, watchdog, kill_process_children


def test_poll_filesystem(app):
    import dummy_module as dm
    mtimes = {}

    assert poll_filesystem(mtimes) == 0
    assert poll_filesystem(mtimes) == 0
    ts_now_1 = time.time()
    os.utime(dm.__file__, (ts_now_1, ts_now_1))
    assert poll_filesystem(mtimes) == 1
    assert poll_filesystem(mtimes) == 0
    time.sleep(0.1)
    ts_now_2 = time.time()
    os.utime(dm.__file__, (ts_now_2, ts_now_1))  # same modified time
    os.utime(dm.submodule01.__file__, (ts_now_2, ts_now_2))
    os.utime(dm.submodule02.__file__, (ts_now_2, ts_now_2))
    assert poll_filesystem(mtimes) == 2
    assert poll_filesystem(mtimes) == 0


def test_watchdog(app):
    import dummy_module as dm
    try:
        watchdog_iter = watchdog(0.2, "python -m examples.simple_server")
        worker1 = next(watchdog_iter)  # Initial worker
        ts_now_1 = time.time()
        os.utime(dm.__file__, (ts_now_1, ts_now_1))
        worker2 = next(watchdog_iter)
        time.sleep(0.1)
        assert worker2.pid != worker1.pid
        assert not worker1.is_alive()
    finally:
        kill_process_children(worker2.pid)
        worker2.terminate()