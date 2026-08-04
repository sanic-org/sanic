import asyncio
import logging

from os import environ
from unittest.mock import Mock, patch

import pytest

from sanic.app import Sanic
from sanic.application.constants import Mode
from sanic.signals import Event
from sanic.worker.loader import AppLoader
from sanic.worker.multiplexer import WorkerMultiplexer
from sanic.worker.process import Worker, WorkerProcess
from sanic.worker.serve import worker_serve


@pytest.fixture
def mock_app():
    app = Mock()
    server_info = Mock()
    server_info.settings = {"app": app}
    app.state.workers = 1
    app.listeners = {"main_process_ready": []}
    app.get_motd_data.return_value = ({"packages": ""}, {})
    app.state.server_info = [server_info]
    return app


def args(app, **kwargs):
    params = {**kwargs}
    params.setdefault("host", "127.0.0.1")
    params.setdefault("port", 9999)
    params.setdefault("app_name", "test_config_app")
    params.setdefault("monitor_publisher", None)
    params.setdefault("app_loader", AppLoader(factory=lambda: app))
    return params


def test_config_app(mock_app: Mock):
    with patch("sanic.worker.serve._serve_http_1"):
        worker_serve(**args(mock_app, config={"FOO": "BAR"}))
    mock_app.update_config.assert_called_once_with({"FOO": "BAR"})


def test_bad_process(mock_app: Mock, caplog):
    environ["SANIC_WORKER_NAME"] = (
        f"{Worker.WORKER_PREFIX}-{WorkerProcess.SERVER_LABEL}-FOO"
    )

    message = "No restart publisher found in worker process"
    with pytest.raises(RuntimeError, match=message):
        worker_serve(**args(mock_app))

    message = "No worker state found in worker process"
    publisher = Mock()
    with caplog.at_level(logging.ERROR):
        worker_serve(**args(mock_app, monitor_publisher=publisher))

    assert ("sanic.error", logging.ERROR, message) in caplog.record_tuples
    publisher.send.assert_called_once_with("__TERMINATE_EARLY__")

    del environ["SANIC_WORKER_NAME"]


def test_has_multiplexer(app: Sanic):
    environ["SANIC_WORKER_NAME"] = (
        f"{Worker.WORKER_PREFIX}-{WorkerProcess.SERVER_LABEL}-FOO"
    )

    Sanic.register_app(app)
    with patch("sanic.worker.serve._serve_http_1"):
        worker_serve(
            **args(app, monitor_publisher=Mock(), worker_state=Mock())
        )
    assert isinstance(app.multiplexer, WorkerMultiplexer)

    del environ["SANIC_WORKER_NAME"]


def test_secondary_app_receives_worker_passthru(app: Sanic):
    secondary = Sanic("secondary")
    app_passthru = {
        secondary.name: {
            "state": {"mode": Mode.DEBUG},
        }
    }
    environ["SANIC_WORKER_NAME"] = (
        f"{Worker.WORKER_PREFIX}-{WorkerProcess.SERVER_LABEL}-FOO"
    )

    try:
        with patch("sanic.worker.serve._serve_http_1"):
            worker_serve(
                **args(
                    app,
                    monitor_publisher=Mock(),
                    worker_state=Mock(),
                    app_passthru=app_passthru,
                )
            )

        async def startup_and_dispatch():
            await secondary._startup()
            await secondary.dispatch(Event.HTTP_LIFECYCLE_BEGIN, inline=True)

        asyncio.run(startup_and_dispatch())
    finally:
        del environ["SANIC_WORKER_NAME"]

    assert secondary.state.is_debug
    assert secondary.config.TOUCHUP is False


@patch("sanic.mixins.startup.WorkerManager")
def test_serve_passes_secondary_app_state(worker_manager: Mock, app: Sanic):
    secondary = Sanic("secondary")
    app.prepare(dev=True)
    secondary.prepare(dev=True)

    with patch("sanic.mixins.startup.configure_socket"):
        Sanic.serve(primary=app)

    worker_kwargs = worker_manager.call_args.args[2]
    secondary_passthru = worker_kwargs["app_passthru"][secondary.name]
    assert secondary_passthru["state"]["mode"] is Mode.DEBUG
    assert secondary_passthru["config"]["ACCESS_LOG"] is True


@patch("sanic.mixins.startup.WorkerManager")
def test_serve_app_implicit(wm: Mock, app):
    app.prepare()
    Sanic.serve()
    wm.call_args[0] == app.state.workers


@patch("sanic.mixins.startup.WorkerManager")
def test_serve_app_explicit(wm: Mock, mock_app):
    Sanic.serve(mock_app)
    wm.call_args[0] == mock_app.state.workers


@patch("sanic.mixins.startup.WorkerManager")
def test_serve_app_loader(wm: Mock, mock_app):
    Sanic.serve(app_loader=AppLoader(factory=lambda: mock_app))
    wm.call_args[0] == mock_app.state.workers
    # Sanic.serve(factory=lambda: mock_app)


@patch("sanic.mixins.startup.WorkerManager")
def test_serve_app_factory(wm: Mock, mock_app):
    Sanic.serve(factory=lambda: mock_app)
    wm.call_args[0] == mock_app.state.workers


@patch("sanic.mixins.startup.WorkerManager")
@pytest.mark.parametrize("config", (True, False))
def test_serve_with_inspector(
    WorkerManager: Mock, mock_app: Mock, config: bool
):
    Inspector = Mock()
    mock_app.config.INSPECTOR = config
    mock_app.inspector_class = Inspector
    inspector = Mock()
    Inspector.return_value = inspector
    WorkerManager.return_value = WorkerManager

    Sanic.serve(mock_app)

    if config:
        Inspector.assert_called_once()
        WorkerManager.manage.assert_called_once_with(
            "Inspector", inspector, {}, transient=False
        )
    else:
        Inspector.assert_not_called()
        WorkerManager.manage.assert_not_called()
