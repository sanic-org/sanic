try:  # no cov
    from ujson import dumps
except ModuleNotFoundError:  # no cov
    from json import dumps  # type: ignore

from datetime import datetime
from unittest.mock import Mock, patch
from urllib.error import URLError

import pytest

from sanic_testing import TestManager

from sanic.cli.inspector_client import InspectorClient
from sanic.helpers import Default
from sanic.log import Colors
from sanic.worker.inspector import Inspector


DATA = {
    "info": {
        "packages": ["foo"],
    },
    "extra": {
        "more": "data",
    },
    "workers": {"Worker-Name": {"some": "state"}},
}
FULL_SERIALIZED = dumps({"result": DATA})
OUT_SERIALIZED = dumps(DATA)


class FooInspector(Inspector):
    async def foo(self, bar):
        return f"bar is {bar}"


@pytest.fixture
def publisher():
    publisher = Mock()
    return publisher


@pytest.fixture
def inspector(publisher):
    inspector = FooInspector(
        publisher, {}, {}, "localhost", 9999, "", Default(), Default()
    )
    inspector(False)
    return inspector


@pytest.fixture
def http_client(inspector):
    manager = TestManager(inspector.app)
    return manager.test_client


@pytest.mark.parametrize("command", ("info",))
@patch("sanic.cli.inspector_client.sys.stdout.write")
def test_send_inspect(write, urlopen, command: str):
    urlopen.read.return_value = FULL_SERIALIZED.encode()
    InspectorClient("localhost", 9999, False, False, None).do(command)
    write.assert_called()
    write.reset_mock()
    InspectorClient("localhost", 9999, False, True, None).do(command)
    write.assert_called_with(OUT_SERIALIZED + "\n")


@patch("sanic.cli.inspector_client.sys")
def test_send_inspect_conn_refused(sys: Mock, urlopen):
    urlopen.side_effect = URLError("")
    InspectorClient("localhost", 9999, False, False, None).do("info")

    message = (
        f"{Colors.RED}Could not connect to inspector at: "
        f"{Colors.YELLOW}http://localhost:9999{Colors.END}\n"
        "Either the application is not running, or it did not start "
        "an inspector instance.\n<urlopen error >\n"
    )
    sys.exit.assert_called_once_with(1)
    sys.stderr.write.assert_called_once_with(message)


def test_run_inspector_reload(publisher, http_client):
    _, response = http_client.post("/reload")
    assert response.status == 200
    publisher.send.assert_called_once_with("__ALL_PROCESSES__:")


def test_run_inspector_reload_zero_downtime(publisher, http_client):
    _, response = http_client.post("/reload", json={"zero_downtime": True})
    assert response.status == 200
    publisher.send.assert_called_once_with("__ALL_PROCESSES__::STARTUP_FIRST")


def test_run_inspector_shutdown(publisher, http_client):
    _, response = http_client.post("/shutdown")
    assert response.status == 200
    publisher.send.assert_called_once_with("__TERMINATE__")


def test_run_inspector_scale(publisher, http_client):
    _, response = http_client.post("/scale", json={"replicas": 4})
    assert response.status == 200
    publisher.send.assert_called_once_with("__SCALE__:4")


def test_run_inspector_arbitrary(http_client):
    _, response = http_client.post("/foo", json={"bar": 99})
    assert response.status == 200
    assert response.json == {"meta": {"action": "foo"}, "result": "bar is 99"}


def test_state_to_json():
    now = datetime.now()
    now_iso = now.isoformat()
    app_info = {"app": "hello"}
    worker_state = {"Test": {"now": now, "nested": {"foo": now}}}
    inspector = Inspector(
        Mock(), app_info, worker_state, "", 0, "", Default(), Default()
    )
    state = inspector._state_to_json()

    assert state == {
        "info": app_info,
        "workers": {"Test": {"now": now_iso, "nested": {"foo": now_iso}}},
    }


def test_run_inspector_authentication():
    inspector = Inspector(
        Mock(), {}, {}, "", 0, "super-secret", Default(), Default()
    )(False)
    manager = TestManager(inspector.app)
    _, response = manager.test_client.get("/")
    assert response.status == 401
    _, response = manager.test_client.get(
        "/", headers={"Authorization": "Bearer super-secret"}
    )
    assert response.status == 200
