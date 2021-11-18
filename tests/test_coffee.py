import logging

from unittest.mock import patch

import pytest

from sanic.application.logo import COFFEE_LOGO, get_logo
from sanic.exceptions import SanicException


def has_sugar(value):
    if value:
        raise SanicException("I said no sugar please")

    return False


@pytest.mark.parametrize("sugar", (True, False))
def test_no_sugar(sugar):
    if sugar:
        with pytest.raises(SanicException):
            assert has_sugar(sugar)
    else:
        assert not has_sugar(sugar)


def test_get_logo_returns_expected_logo():
    with patch("sys.stdout.isatty") as isatty:
        isatty.return_value = True
        logo = get_logo(coffee=True)
    assert logo is COFFEE_LOGO


def test_logo_true(app, caplog):
    @app.after_server_start
    async def shutdown(*_):
        app.stop()

    with patch("sys.stdout.isatty") as isatty:
        isatty.return_value = True
        with caplog.at_level(logging.DEBUG):
            app.make_coffee()

    # Only in the regular logo
    assert "    ▄███ █████ ██    " not in caplog.text

    # Only in the coffee logo
    assert "    ██       ██▀▀▄   " in caplog.text
