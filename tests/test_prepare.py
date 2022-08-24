import logging
import os

from pathlib import Path
from unittest.mock import Mock

import pytest

from sanic import Sanic
from sanic.application.state import ApplicationServerInfo


@pytest.fixture(autouse=True)
def no_skip():
    should_auto_reload = Sanic.should_auto_reload
    Sanic.should_auto_reload = Mock(return_value=False)
    yield
    Sanic._app_registry = {}
    Sanic.should_auto_reload = should_auto_reload
    try:
        del os.environ["SANIC_MOTD_OUTPUT"]
    except KeyError:
        ...


def get_primary(app: Sanic) -> ApplicationServerInfo:
    return app.state.server_info[0]


def test_dev(app: Sanic):
    app.prepare(dev=True)

    assert app.state.is_debug
    assert app.state.auto_reload


def test_motd_display(app: Sanic):
    app.prepare(motd_display={"foo": "bar"})

    assert app.config.MOTD_DISPLAY["foo"] == "bar"
    del app.config.MOTD_DISPLAY["foo"]


@pytest.mark.parametrize("dirs", ("./foo", ("./foo", "./bar")))
def test_reload_dir(app: Sanic, dirs, caplog):
    messages = []
    with caplog.at_level(logging.WARNING):
        app.prepare(reload_dir=dirs)

    if isinstance(dirs, str):
        dirs = (dirs,)
        for d in dirs:
            assert Path(d) in app.state.reload_dirs
            messages.append(
                f"Directory {d} could not be located",
            )

    for message in messages:
        assert ("sanic.root", logging.WARNING, message) in caplog.record_tuples


def test_fast(app: Sanic, caplog):
    @app.after_server_start
    async def stop(app, _):
        app.stop()

    try:
        workers = len(os.sched_getaffinity(0))
    except AttributeError:
        workers = os.cpu_count() or 1

    with caplog.at_level(logging.INFO):
        app.prepare(fast=True)

    assert app.state.fast
    assert app.state.workers == workers

    messages = [m[2] for m in caplog.record_tuples]
    assert f"mode: production, goin' fast w/ {workers} workers" in messages
