import os
import sys

from unittest.mock import patch

import pytest

from sanic.application.logo import (
    BASE_LOGO,
    COLOR_LOGO,
    FULL_COLOR_LOGO,
    get_logo,
)


@pytest.mark.parametrize(
    "tty,full,expected",
    (
        (True, False, COLOR_LOGO),
        (True, True, FULL_COLOR_LOGO),
        (False, False, BASE_LOGO),
        (False, True, BASE_LOGO),
    ),
)
def test_get_logo_returns_expected_logo(tty, full, expected):
    with patch("sys.stdout.isatty") as isatty:
        isatty.return_value = tty
        logo = get_logo(full=full)
    assert logo is expected


def test_get_logo_returns_no_colors_on_apple_terminal():
    platform = sys.platform
    sys.platform = "darwin"
    os.environ["TERM_PROGRAM"] = "Apple_Terminal"
    with patch("sys.stdout.isatty") as isatty:
        isatty.return_value = False
        logo = get_logo()
    assert "\033" not in logo
    sys.platform = platform
    del os.environ["TERM_PROGRAM"]
