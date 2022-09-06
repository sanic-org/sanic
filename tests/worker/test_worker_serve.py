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
    app.state.server_info = [Mock()]
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
