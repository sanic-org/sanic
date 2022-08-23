from unittest.mock import Mock

import pytest

from aioquic.h3.connection import H3Connection
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
from sanic.models.server_types import ConnInfo
from sanic.response import empty, json
from sanic.server.protocols.http_protocol import Http3Protocol


try:
    from unittest.mock import AsyncMock
except ImportError:
    from tests.asyncmock import AsyncMock  # type: ignore

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
    receiver.response = Mock()
    resp = receiver.respond(response)

    assert receiver.response is resp
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
    assert receiver.request.stream_id == 1
    assert receiver.request.path == "/location"
    assert receiver.request.method == "GET"
    assert receiver.request.headers["foo"] == "bar"
    assert receiver.request.body == b"foobar"


async def test_send_headers(app: Sanic, http_request: Request):
    send_headers_mock = Mock()
    existing_send_headers = H3Connection.send_headers
    receiver = generate_http_receiver(app, http_request)
    receiver.protocol.quic_event_received(
        ProtocolNegotiated(alpn_protocol="h3")
    )

    http_request._protocol = receiver.protocol

    def send_headers(*args, **kwargs):
        send_headers_mock(*args, **kwargs)
        return existing_send_headers(
            receiver.protocol.connection, *args, **kwargs
        )

    receiver.protocol.connection.send_headers = send_headers
    receiver.head_only = False
    response = json({}, status=201, headers={"foo": "bar"})

    with pytest.raises(RuntimeError, match="no response"):
        receiver.send_headers()

    receiver.response = response
    receiver.send_headers()

    assert receiver.headers_sent
    assert receiver.stage is Stage.RESPONSE
    send_headers_mock.assert_called_once_with(
        stream_id=0,
        headers=[
            (b":status", b"201"),
            (b"foo", b"bar"),
            (b"content-length", b"2"),
            (b"content-type", b"application/json"),
        ],
    )


def test_multiple_streams(app):
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
    http3.http_event_received(
        HeadersReceived(
            [
                (b":method", b"GET"),
                (b":path", b"/location"),
                (b":scheme", b"https"),
                (b":authority", b"localhost:8443"),
                (b"foo", b"bar"),
            ],
            2,
            False,
        )
    )

    receiver1 = http3.get_receiver_by_stream_id(1)
    receiver2 = http3.get_receiver_by_stream_id(2)
    assert len(http3.receivers) == 2
    assert isinstance(receiver1, HTTPReceiver)
    assert isinstance(receiver2, HTTPReceiver)
    assert receiver1 is not receiver2


def test_request_stream_id(app):
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
    receiver = http3.get_receiver_by_stream_id(1)

    assert isinstance(receiver.request, Request)
    assert receiver.request.stream_id == 1


def test_request_conn_info(app):
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
    receiver = http3.get_receiver_by_stream_id(1)

    assert isinstance(receiver.request.conn_info, ConnInfo)
