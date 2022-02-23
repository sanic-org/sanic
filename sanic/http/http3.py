from __future__ import annotations

import asyncio

from abc import ABC, abstractmethod
from ssl import SSLContext
from typing import TYPE_CHECKING, Callable, Dict, Optional, Tuple, Union

from aioquic.h0.connection import H0_ALPN, H0Connection
from aioquic.h3.connection import H3_ALPN, H3Connection
from aioquic.h3.events import (
    DatagramReceived,
    DataReceived,
    H3Event,
    HeadersReceived,
    WebTransportStreamDataReceived,
)
from aioquic.quic.configuration import QuicConfiguration

# from aioquic.quic.events import (
#     DatagramFrameReceived,
#     ProtocolNegotiated,
#     QuicEvent,
# )
from aioquic.tls import SessionTicket

from sanic.compat import Header
from sanic.exceptions import SanicException
from sanic.http.tls import CertSimple


if TYPE_CHECKING:
    from sanic import Sanic
    from sanic.request import Request
    from sanic.response import BaseHTTPResponse, HTTPResponse
    from sanic.server.protocols.http_protocol import Http3Protocol

# from sanic.compat import Header
from sanic.http.constants import Stage

# from sanic.application.state import Mode
from sanic.log import Colors, logger


HttpConnection = Union[H0Connection, H3Connection]


class Transport:
    ...


class Receiver(ABC):
    def __init__(self, transmit, protocol, request: Request) -> None:
        self.transmit = transmit
        self.protocol = protocol
        self.request = request
        self.queue: asyncio.Queue[Tuple[bytes, bool]] = asyncio.Queue()

    @abstractmethod
    async def run(self):
        ...


class HTTPReceiver(Receiver):
    stage: Stage

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.request_body = None
        self.stage = Stage.IDLE
        self.headers_sent = False

    async def run(self):
        self.stage = Stage.HANDLER

        logger.info(f"Request received: {self.request}")
        await self.protocol.request_handler(self.request)

        self.stage = Stage.RESPONSE

        while self.stage is Stage.RESPONSE:
            if not self.headers_sent:
                self.send_headers()
            data, end_stream = await self.queue.get()

            # Chunked
            size = len(data)
            if end_stream:
                data = (
                    b"%x\r\n%b\r\n0\r\n\r\n" % (size, data)
                    if size
                    else b"0\r\n\r\n"
                )
            elif size:
                data = b"%x\r\n%b\r\n" % (size, data)

            self.protocol.connection.send_data(
                stream_id=self.request.stream_id,
                data=data,
                end_stream=end_stream,
            )
            self.transmit()

            if end_stream:
                self.stage = Stage.IDLE

    def send_headers(self) -> None:
        response = self.request.stream.response
        self.protocol.connection.send_headers(
            stream_id=self.request.stream_id,
            headers=[
                (b":status", str(response.status).encode()),
                *(
                    (k.encode(), v.encode())
                    for k, v in response.headers.items()
                ),
            ],
        )
        self.headers_sent = True

    async def respond(self, response: BaseHTTPResponse) -> BaseHTTPResponse:
        print(f"{Colors.BLUE}[respond]: {Colors.GREEN}{response=}{Colors.END}")
        self.response, response.stream = response, self

        return response

    async def send(self, data: bytes, end_stream: bool) -> None:
        print(
            f"{Colors.BLUE}[send]: {Colors.GREEN}{data=} {end_stream=}{Colors.END}"
        )
        self.queue.put_nowait((data, end_stream))


class WebsocketReceiver(Receiver):
    async def run(self):
        ...


class WebTransportReceiver(Receiver):
    async def run(self):
        ...


class Http3:
    HANDLER_PROPERTY_MAPPING = {
        DataReceived: "stream_id",
        HeadersReceived: "stream_id",
        DatagramReceived: "flow_id",
        WebTransportStreamDataReceived: "session_id",
    }

    def __init__(
        self,
        protocol: Http3Protocol,
        transmit: Callable[[], None],
    ) -> None:
        # self.request_body = None
        # self.request: Optional[Request] = None
        self.protocol = protocol
        self.transmit = transmit
        self.receivers: Dict[int, Receiver] = {}

    def http_event_received(self, event: H3Event) -> None:
        print(
            f"{Colors.BLUE}[http_event_received]: "
            f"{Colors.YELLOW}{event}{Colors.END}"
        )
        receiver, created_new = self.get_or_make_receiver(event)
        print(f"{receiver=}")

        if isinstance(event, HeadersReceived) and created_new:
            asyncio.ensure_future(receiver.run())
        else:
            print(f"{Colors.RED}DOING NOTHING{Colors.END}")

    def get_or_make_receiver(self, event: H3Event) -> Tuple[Receiver, bool]:
        if (
            isinstance(event, HeadersReceived)
            and event.stream_id not in self.receivers
        ):
            request = self._make_request(event)
            receiver = HTTPReceiver(self.transmit, self.protocol, request)
            request.stream = receiver

            self.receivers[event.stream_id] = receiver
            return receiver, True
        else:
            ident = getattr(event, self.HANDLER_PROPERTY_MAPPING[type(event)])
            return self.receivers[ident], False

    def get_receiver_by_stream_id(self, stream_id: int) -> Receiver:
        return self.receivers[stream_id]

    def _make_request(self, event: HeadersReceived) -> Request:
        method_header, path_header, *rem = event.headers
        headers = Header(((k.decode(), v.decode()) for k, v in rem))
        method = method_header[1].decode()
        path = path_header[1]
        scheme = headers.pop(":scheme")
        authority = headers.pop(":authority")
        print(f"{headers=}")
        print(f"{method=}")
        print(f"{path=}")
        print(f"{scheme=}")
        print(f"{authority=}")
        if authority:
            headers["host"] = authority

        request = self.protocol.request_class(
            path, headers, "3", method, Transport(), self.protocol.app, b""
        )
        request._stream_id = event.stream_id
        print(f"{request=}")
        return request


class SessionTicketStore:
    """
    Simple in-memory store for session tickets.
    """

    def __init__(self) -> None:
        self.tickets: Dict[bytes, SessionTicket] = {}

    def add(self, ticket: SessionTicket) -> None:
        self.tickets[ticket.ticket] = ticket

    def pop(self, label: bytes) -> Optional[SessionTicket]:
        return self.tickets.pop(label, None)


def get_config(app: Sanic, ssl: SSLContext):
    if not isinstance(ssl, CertSimple):
        raise SanicException("SSLContext is not CertSimple")

    config = QuicConfiguration(
        alpn_protocols=H3_ALPN + H0_ALPN + ["siduck"],
        is_client=False,
        max_datagram_frame_size=65536,
    )
    password = app.config.TLS_CERT_PASSWORD or None
    config.load_cert_chain(
        ssl.sanic["cert"], ssl.sanic["key"], password=password
    )

    return config


def get_ticket_store():
    return SessionTicketStore()
