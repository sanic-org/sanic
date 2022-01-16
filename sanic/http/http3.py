from __future__ import annotations

import asyncio

from abc import ABC
from ssl import SSLContext
from typing import TYPE_CHECKING, Callable, Dict, Optional, Union

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
    from sanic.response import BaseHTTPResponse
    from sanic.server.protocols.http_protocol import Http3Protocol

# from sanic.compat import Header
# from sanic.application.state import Mode
from sanic.log import logger


HttpConnection = Union[H0Connection, H3Connection]


class Transport:
    ...


class Receiver(ABC):
    def __init__(self, transmit, protocol, request) -> None:
        self.transmit = transmit
        self.protocol = protocol
        self.request = request


class HTTPReceiver(Receiver):
    async def respond(self):
        logger.info(f"Request received: {self.request}")
        await self.protocol.app.handle_request(self.request)


class WebsocketReceiver(Receiver):
    ...


class WebTransportReceiver(Receiver):
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
        self.request_body = None
        self.request: Optional[Request] = None
        self.protocol = protocol
        self.transmit = transmit
        self.receivers: Dict[int, Receiver] = {}

    def http_event_received(self, event: H3Event) -> None:
        print("[http_event_received]:", event)
        receiver = self.get_or_make_receiver(event)
        print(f"{receiver=}")

        #     asyncio.ensure_future(handler(request))

    def get_or_make_receiver(self, event: H3Event) -> Receiver:
        if (
            isinstance(event, HeadersReceived)
            and event.stream_id not in self.receivers
        ):
            self.request = self._make_request(event)
            receiver = HTTPReceiver(self.transmit, self.protocol, self.request)
            self.receivers[event.stream_id] = receiver
            asyncio.ensure_future(receiver.respond())
        else:
            ident = getattr(event, self.HANDLER_PROPERTY_MAPPING[type(event)])
            return self.receivers[ident]

    def _make_request(self, event: HeadersReceived) -> Request:
        method, path, *rem = event.headers
        headers = Header(((k.decode(), v.decode()) for k, v in rem))
        method = method[1].decode()
        path = path[1]
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
        request.stream = self
        print(f"{request=}")
        return request

    async def respond(self, response: BaseHTTPResponse) -> BaseHTTPResponse:
        print(f"[respond]: {response=}")
        response.headers.update({"foo": "bar"})
        self.response, response.stream = response, self

        # Need more appropriate place to send these
        self.protocol.connection.send_headers(
            stream_id=0,
            headers=[
                (b":status", str(self.response.status).encode()),
                *(
                    (k.encode(), v.encode())
                    for k, v in self.response.headers.items()
                ),
            ],
        )
        # TEMP
        await self.drain(response)

        return response

    async def drain(self, response: BaseHTTPResponse) -> None:
        await self.send(response.body, False)

    async def send(self, data: bytes, end_stream: bool) -> None:
        print(f"[send]: {data=} {end_stream=}")
        print(self.response.headers)
        self.protocol.connection.send_data(
            stream_id=0,
            data=data,
            end_stream=end_stream,
        )
        self.transmit()


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
    # TODO:
    # - add password kwarg, read from config.TLS_CERT_PASSWORD
    config.load_cert_chain(ssl.sanic["cert"], ssl.sanic["key"])

    return config


def get_ticket_store():
    return SessionTicketStore()
