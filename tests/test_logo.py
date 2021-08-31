import asyncio
import logging

from sanic_testing.testing import PORT

from sanic.config import BASE_LOGO


def test_logo_base(app, run_startup):
    logs = run_startup(app)

    assert logs[0][1] == logging.DEBUG
    assert logs[0][2] == BASE_LOGO


def test_logo_false(app, caplog, run_startup):
    app.config.LOGO = False

    logs = run_startup(app)

    banner, port = logs[0][2].rsplit(":", 1)
    assert logs[0][1] == logging.INFO
    assert banner == "Goin' Fast @ http://127.0.0.1"
    assert int(port) > 0


def test_logo_true(app, run_startup):
    app.config.LOGO = True

    logs = run_startup(app)

    assert logs[0][1] == logging.DEBUG
    assert logs[0][2] == BASE_LOGO


def test_logo_custom(app, run_startup):
    app.config.LOGO = "My Custom Logo"

    logs = run_startup(app)

    assert logs[0][1] == logging.DEBUG
    assert logs[0][2] == "My Custom Logo"
