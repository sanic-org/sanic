import logging
import platform

from unittest.mock import Mock

from sanic import __version__
from sanic.application.logo import BASE_LOGO
from sanic.application.motd import MOTDTTY


def test_logo_base(app, run_startup):
    logs = run_startup(app)

    assert logs[0][1] == logging.DEBUG
    assert logs[0][2] == BASE_LOGO


def test_logo_false(app, run_startup):
    app.config.LOGO = False

    logs = run_startup(app)

    banner, port = logs[1][2].rsplit(":", 1)
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


def test_motd_with_expected_info(app, run_startup):
    logs = run_startup(app)

    assert logs[1][2] == f"Sanic v{__version__}"
    assert logs[3][2] == "mode: debug, single worker"
    assert logs[4][2] == "server: sanic"
    assert logs[5][2] == f"python: {platform.python_version()}"
    assert logs[6][2] == f"platform: {platform.platform()}"


def test_motd_init():
    _orig = MOTDTTY.set_variables
    MOTDTTY.set_variables = Mock()
    motd = MOTDTTY(None, "", {}, {})

    motd.set_variables.assert_called_once()
    MOTDTTY.set_variables = _orig


def test_motd_display(caplog):
    motd = MOTDTTY("       foobar        ", "", {"one": "1"}, {"two": "2"})

    with caplog.at_level(logging.INFO):
        motd.display()

    version_line = f"Sanic v{__version__}".center(motd.centering_length)
    assert (
        "".join(caplog.messages)
        == f"""
  ┌────────────────────────────────┐
  │ {version_line} │
  │                                │
  ├───────────────────────┬────────┤
  │        foobar         │ one: 1 │
  |                       ├────────┤
  │                       │ two: 2 │
  └───────────────────────┴────────┘
"""
    )
