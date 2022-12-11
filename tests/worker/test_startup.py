from unittest.mock import patch

import pytest

from sanic import Sanic


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
