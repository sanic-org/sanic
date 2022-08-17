from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from sanic import Sanic, response
from sanic.exceptions import BadURL, SanicException
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
    request.app.config.REQUEST_ID_HEADER = "foo"

    for _ in range(10):
        request.id
    Request.generate_id.assert_called_once_with(request)


def test_request_id_defaults_uuid():
    request = Request(b"/", {}, None, "GET", None, Mock())
    request.app.config.REQUEST_ID_HEADER = "foo"

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
    assert request.route is list(app.router.routes)[0]


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


def test_ipv6_address_is_not_wrapped(app):
    @app.get("/")
    async def get(request):
        return response.json(
            {
                "client_ip": request.conn_info.client_ip,
                "client": request.conn_info.client,
            }
        )

    request, resp = app.test_client.get("/", host="::1")

    assert request.route is list(app.router.routes)[0]
    assert resp.json["client"] == "[::1]"
    assert resp.json["client_ip"] == "::1"
    assert request.ip == "::1"


def test_request_accept():
    app = Sanic("req-generator")

    @app.get("/")
    async def get(request):
        return response.empty()

    request, _ = app.test_client.get(
        "/",
        headers={
            "Accept": "text/*, text/plain, text/plain;format=flowed, */*"
        },
    )
    assert request.accept == [
        "text/plain;format=flowed",
        "text/plain",
        "text/*",
        "*/*",
    ]

    request, _ = app.test_client.get(
        "/",
        headers={
            "Accept": (
                "text/plain; q=0.5, text/html, text/x-dvi; q=0.8, text/x-c"
            )
        },
    )
    assert request.accept == [
        "text/html",
        "text/x-c",
        "text/x-dvi; q=0.8",
        "text/plain; q=0.5",
    ]


def test_bad_url_parse():
    message = "Bad URL: my.redacted-domain.com:443"
    with pytest.raises(BadURL, match=message):
        Request(
            b"my.redacted-domain.com:443",
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
        )


def test_request_scope_raises_exception_when_no_asgi():
    app = Sanic("no_asgi")

    @app.get("/")
    async def get(request):
        return request.scope

    request, response = app.test_client.get("/")
    assert response.status == 500
    with pytest.raises(NotImplementedError):
        _ = request.scope


@pytest.mark.asyncio
async def test_request_scope_is_not_none_when_running_in_asgi(app):
    @app.get("/")
    async def get(request):
        return response.empty()

    request, _ = await app.asgi_client.get("/")

    assert request.scope is not None
    assert request.scope["method"].lower() == "get"
    assert request.scope["path"].lower() == "/"


def test_cannot_get_request_outside_of_cycle():
    with pytest.raises(SanicException, match="No current request"):
        Request.get_current()


def test_get_current_request(app):
    @app.get("/")
    async def get(request):
        return response.json({"same": request is Request.get_current()})

    _, resp = app.test_client.get("/")
    assert resp.json["same"]


def test_request_stream_id(app):
    @app.get("/")
    async def get(request):
        try:
            request.stream_id
        except Exception as e:
            return response.text(str(e))

    _, resp = app.test_client.get("/")
    assert resp.text == "Stream ID is only a property of a HTTP/3 request"


@pytest.mark.parametrize(
    "method,safe",
    (
        ("DELETE", False),
        ("GET", True),
        ("HEAD", True),
        ("OPTIONS", True),
        ("PATCH", False),
        ("POST", False),
        ("PUT", False),
    ),
)
def test_request_safe(method, safe):
    request = Request(b"/", {}, None, method, None, None)
    assert request.is_safe is safe


@pytest.mark.parametrize(
    "method,idempotent",
    (
        ("DELETE", True),
        ("GET", True),
        ("HEAD", True),
        ("OPTIONS", True),
        ("PATCH", False),
        ("POST", False),
        ("PUT", True),
    ),
)
def test_request_idempotent(method, idempotent):
    request = Request(b"/", {}, None, method, None, None)
    assert request.is_idempotent is idempotent


@pytest.mark.parametrize(
    "method,cacheable",
    (
        ("DELETE", False),
        ("GET", True),
        ("HEAD", True),
        ("OPTIONS", False),
        ("PATCH", False),
        ("POST", False),
        ("PUT", False),
    ),
)
def test_request_cacheable(method, cacheable):
    request = Request(b"/", {}, None, method, None, None)
    assert request.is_cacheable is cacheable
