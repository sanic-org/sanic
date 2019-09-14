import time
import os

from sanic.reloader_helpers import poll_filesystem


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