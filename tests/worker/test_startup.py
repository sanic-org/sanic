from unittest.mock import patch

import pytest

from sanic import Sanic


@pytest.mark.parametrize(
    "start_method,platform,reload,expected",
    (
        (None, "linux", False, "fork"),
        (None, "linux", True, "spawn"),
        (None, "other", False, "spawn"),
        (None, "other", True, "spawn"),
        ("fork", "linux", False, "fork"),
        ("fork", "linux", True, "fork"),
        ("fork", "other", False, "fork"),
        ("fork", "other", True, "fork"),
        ("forkserver", "linux", False, "forkserver"),
        ("forkserver", "linux", True, "forkserver"),
        ("forkserver", "other", False, "forkserver"),
        ("forkserver", "other", True, "forkserver"),
        ("spawn", "linux", False, "spawn"),
        ("spawn", "linux", True, "spawn"),
        ("spawn", "other", False, "spawn"),
        ("spawn", "other", True, "spawn"),
    ),
)
def test_get_context(start_method, platform, reload, expected):
    if start_method:
        Sanic.start_method = start_method
    with patch("sys.platform", platform):
        with patch("sanic.Sanic.should_auto_reload") as should:
            should.return_value = reload
            assert Sanic.should_auto_reload() is reload
            assert Sanic._get_startup_method() == expected
