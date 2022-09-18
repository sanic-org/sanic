import logging
import os
import platform
import sys

from unittest.mock import Mock, patch

import pytest

from sanic import __version__
from sanic.application.logo import BASE_LOGO
from sanic.application.motd import MOTD, MOTDTTY


@pytest.fixture(autouse=True)
def reset():
    try:
        del os.environ["SANIC_MOTD_OUTPUT"]
    except KeyError:
        ...


def test_logo_base(app, run_startup):
    logs = run_startup(app)

    assert logs[0][1] == logging.DEBUG
    assert logs[0][2] == BASE_LOGO


def test_motd_with_expected_info(app, run_startup):
    logs = run_startup(app)

    assert logs[1][2] == f"Sanic v{__version__}"
    assert logs[3][2] == "mode: debug, single worker"
    assert logs[4][2] == "server: sanic, HTTP/1.1"
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


@pytest.mark.skipif(sys.version_info < (3, 8), reason="Not on 3.7")
def test_reload_dirs(app):
    app.config.LOGO = None
    app.config.MOTD = True
    app.config.AUTO_RELOAD = True

    with patch.object(MOTD, "output") as mock:
        app.prepare(
            reload_dir="./", auto_reload=True, motd_display={"foo": "bar"}
        )
    mock.assert_called()
    assert mock.call_args.args[2]["auto-reload"] == f"enabled, {os.getcwd()}"
    assert mock.call_args.args[3] == {"foo": "bar"}
