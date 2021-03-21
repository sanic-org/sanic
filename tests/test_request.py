from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from sanic import Sanic, response
from sanic.request import Request, uuid
from sanic.server import HttpProtocol


def test_no_request_id_not_called(monkeypatch):
    monkeypatch.setattr(uuid, "uuid4", Mock())
    request = Request(b"/", {}, None, "GET", None, None)

    assert request._id is None
    uuid.uuid4.assert_not_called()


def test_request_id_generates_from_request(monkeypatch):
    monkeypatch.setattr(Request, "generate_id", Mock())
    Request.generate_id.return_value = 1
    request = Request(b"/", {}, None, "GET", None, Mock())

    for _ in range(10):
        request.id
    Request.generate_id.assert_called_once_with(request)


def test_request_id_defaults_uuid():
    request = Request(b"/", {}, None, "GET", None, Mock())

    assert isinstance(request.id, UUID)

    # Makes sure that it has been cached and not called multiple times
    assert request.id == request.id == request._id


def test_name_none():
    request = Request(b"/", {}, None, "GET", None, None)

    assert request.name is None


def test_name_from_route():
    request = Request(b"/", {}, None, "GET", None, None)
    route = Mock()
    request.route = route

    assert request.name == route.name


def test_name_from_set():
    request = Request(b"/", {}, None, "GET", None, None)
    request._name = "foo"

    assert request.name == "foo"


@pytest.mark.parametrize(
    "request_id,expected_type",
    (
        (99, int),
        (uuid4(), UUID),
        ("foo", str),
    ),
)
def test_request_id(request_id, expected_type):
    app = Sanic("req-generator")

    @app.get("/")
    async def get(request):
        return response.empty()

    request, _ = app.test_client.get(
        "/", headers={"X-REQUEST-ID": f"{request_id}"}
    )
    assert request.id == request_id
    assert type(request.id) == expected_type


def test_custom_generator():
    REQUEST_ID = 99

    class FooRequest(Request):
        @classmethod
        def generate_id(cls, request):
            return int(request.headers["some-other-request-id"]) * 2

    app = Sanic("req-generator", request_class=FooRequest)

    @app.get("/")
    async def get(request):
        return response.empty()

    request, _ = app.test_client.get(
        "/", headers={"SOME-OTHER-REQUEST-ID": f"{REQUEST_ID}"}
    )
    assert request.id == REQUEST_ID * 2


def test_route_assigned_to_request(app):
    @app.get("/")
    async def get(request):
        return response.empty()

    request, _ = app.test_client.get("/")
    assert request.route is list(app.router.routes.values())[0]


def test_protocol_attribute(app):
    retrieved = None

    @app.get("/")
    async def get(request):
        nonlocal retrieved
        retrieved = request.protocol
        return response.empty()

    headers = {"Connection": "keep-alive"}
    _ = app.test_client.get("/", headers=headers)

    assert isinstance(retrieved, HttpProtocol)
