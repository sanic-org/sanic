from unittest.mock import patch

import pytest, sys

from sanic import Sanic

from multiprocessing import Queue, set_start_method


@pytest.mark.parametrize(
    "start_method,platform,expected",
    (
        (None, "linux", "spawn"),
        (None, "other", "spawn"),
        ("fork", "linux", "fork"),
        ("fork", "other", "fork"),
        ("forkserver", "linux", "forkserver"),
        ("forkserver", "other", "forkserver"),
        ("spawn", "linux", "spawn"),
        ("spawn", "other", "spawn"),
    ),
)
def test_get_context(start_method, platform, expected):
    if start_method:
        Sanic.start_method = start_method
    with patch("sys.platform", platform):
        assert Sanic._get_startup_method() == expected


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Only test on Linux")
def test_set_startup_catch():
    Sanic.START_METHOD_SET = False
    set_start_method("fork", force=True)
    Sanic.test_mode = False
    Sanic._set_startup_method()
    Sanic.test_mode = True
