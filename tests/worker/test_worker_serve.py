from os import environ
from unittest.mock import Mock, patch

import pytest

from sanic.app import Sanic
from sanic.worker.loader import AppLoader
from sanic.worker.multiplexer import WorkerMultiplexer
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


def test_bad_process(mock_app: Mock):
    environ["SANIC_WORKER_NAME"] = "FOO"

    message = "No restart publisher found in worker process"
    with pytest.raises(RuntimeError, match=message):
        worker_serve(**args(mock_app))

    message = "No worker state found in worker process"
    with pytest.raises(RuntimeError, match=message):
        worker_serve(**args(mock_app, monitor_publisher=Mock()))

    del environ["SANIC_WORKER_NAME"]


def test_has_multiplexer(app: Sanic):
    environ["SANIC_WORKER_NAME"] = "FOO"

    Sanic.register_app(app)
    with patch("sanic.worker.serve._serve_http_1"):
        worker_serve(
            **args(app, monitor_publisher=Mock(), worker_state=Mock())
        )
    assert isinstance(app.multiplexer, WorkerMultiplexer)

    del environ["SANIC_WORKER_NAME"]


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
@patch("sanic.mixins.startup.Inspector")
@pytest.mark.parametrize("config", (True, False))
def test_serve_with_inspector(
    Inspector: Mock, WorkerManager: Mock, mock_app: Mock, config: bool
):
    mock_app.config.INSPECTOR = config
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
