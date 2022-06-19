from unittest.mock import AsyncMock, Mock

import pytest

from aioquic.h3.events import DataReceived, HeadersReceived
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.connection import QuicConnection
from aioquic.quic.events import ProtocolNegotiated

from sanic import Request, Sanic
from sanic.compat import Header
from sanic.config import DEFAULT_CONFIG
from sanic.exceptions import PayloadTooLarge
from sanic.http.constants import Stage
from sanic.http.http3 import Http3, HTTPReceiver
from sanic.response import empty
from sanic.server.protocols.http_protocol import Http3Protocol


pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
async def setup(app: Sanic):
    @app.get("/")
    async def handler(*_):
        return empty()

    app.router.finalize()
    app.signal_router.finalize()
    app.signal_router.allow_fail_builtin = False


@pytest.fixture
def http_request(app):
    return Request(b"/", Header({}), "3", "GET", Mock(), app)


def generate_protocol(app):
    connection = QuicConnection(configuration=QuicConfiguration())
    connection._ack_delay = 0
    connection._loss = Mock()
    connection._loss.spaces = []
    connection._loss.get_loss_detection_time = lambda: None
    connection.datagrams_to_send = Mock(return_value=[])  # type: ignore
    return Http3Protocol(
        connection,
        app=app,
        stream_handler=None,
    )


def generate_http_receiver(app, http_request) -> HTTPReceiver:
    protocol = generate_protocol(app)
    receiver = HTTPReceiver(
        protocol.transmit,
        protocol,
        http_request,
    )
    http_request.stream = receiver
    return receiver


def test_http_receiver_init(app: Sanic, http_request: Request):
    receiver = generate_http_receiver(app, http_request)
    assert receiver.request_body is None
    assert receiver.stage is Stage.IDLE
    assert receiver.headers_sent is False
    assert receiver.response is None
    assert receiver.request_max_size == DEFAULT_CONFIG["REQUEST_MAX_SIZE"]
    assert receiver.request_bytes == 0


async def test_http_receiver_run_request(app: Sanic, http_request: Request):
    handler = AsyncMock()

    class mock_handle(Sanic):
        handle_request = handler

    app.__class__ = mock_handle
    receiver = generate_http_receiver(app, http_request)
    receiver.protocol.quic_event_received(
        ProtocolNegotiated(alpn_protocol="h3")
    )
    await receiver.run()
    handler.assert_awaited_once_with(receiver.request)


async def test_http_receiver_run_exception(app: Sanic, http_request: Request):
    handler = AsyncMock()

    class mock_handle(Sanic):
        handle_exception = handler

    app.__class__ = mock_handle
    receiver = generate_http_receiver(app, http_request)
    receiver.protocol.quic_event_received(
        ProtocolNegotiated(alpn_protocol="h3")
    )
    exception = Exception("Oof")
    await receiver.run(exception)
    handler.assert_awaited_once_with(receiver.request, exception)

    handler.reset_mock()
    receiver.stage = Stage.REQUEST
    await receiver.run(exception)
    handler.assert_awaited_once_with(receiver.request, exception)


def test_http_receiver_respond(app: Sanic, http_request: Request):
    receiver = generate_http_receiver(app, http_request)
    response = empty()

    receiver.stage = Stage.RESPONSE
    with pytest.raises(RuntimeError, match="Response already started"):
        receiver.respond(response)

    receiver.stage = Stage.HANDLER
    resp = receiver.respond(response)

    assert resp is response
    assert response.stream is receiver


def test_http_receiver_receive_body(app: Sanic, http_request: Request):
    receiver = generate_http_receiver(app, http_request)
    receiver.request_max_size = 4

    receiver.receive_body(b"..")
    assert receiver.request.body == b".."

    receiver.receive_body(b"..")
    assert receiver.request.body == b"...."

    with pytest.raises(
        PayloadTooLarge, match="Request body exceeds the size limit"
    ):
        receiver.receive_body(b"..")


def test_http3_events(app):
    protocol = generate_protocol(app)
    http3 = Http3(protocol, protocol.transmit)
    http3.http_event_received(
        HeadersReceived(
            [
                (b":method", b"GET"),
                (b":path", b"/location"),
                (b":scheme", b"https"),
                (b":authority", b"localhost:8443"),
                (b"foo", b"bar"),
            ],
            1,
            False,
        )
    )
    http3.http_event_received(DataReceived(b"foobar", 1, False))
    receiver = http3.receivers[1]

    assert len(http3.receivers) == 1
    assert receiver.request.path == "/location"
    assert receiver.request.method == "GET"
    assert receiver.request.headers["foo"] == "bar"
    assert receiver.request.body == b"foobar"
