from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, Optional, Union

from aioquic.h0.connection import H0_ALPN, H0Connection
from aioquic.h3.connection import H3_ALPN, H3Connection
from aioquic.h3.events import H3Event

# from aioquic.h3.events import (
#     DatagramReceived,
#     DataReceived,
#     H3Event,
#     HeadersReceived,
#     WebTransportStreamDataReceived,
# )
from aioquic.quic.configuration import QuicConfiguration

# from aioquic.quic.events import (
#     DatagramFrameReceived,
#     ProtocolNegotiated,
#     QuicEvent,
# )
from aioquic.tls import SessionTicket


if TYPE_CHECKING:
    from sanic.request import Request

# from sanic.compat import Header
from sanic.log import logger
from sanic.response import BaseHTTPResponse


HttpConnection = Union[H0Connection, H3Connection]


async def handler(request: Request):
    logger.info(f"Request received: {request}")
    response = await request.app.handle_request(request)
    logger.info(f"Build response: {response=}")


class Transport:
    ...


class Http3:
    def __init__(
        self,
        connection: HttpConnection,
        transmit: Callable[[], None],
    ) -> None:
        self.request_body = None
        self.connection = connection
        self.transmit = transmit

    def http_event_received(self, event: H3Event) -> None:
        print("[http_event_received]:", event)
        # if isinstance(event, HeadersReceived):
        #     method, path, *rem = event.headers
        #     headers = Header(((k.decode(), v.decode()) for k, v in rem))
        #     method = method[1].decode()
        #     path = path[1]
        #     scheme = headers.pop(":scheme")
        #     authority = headers.pop(":authority")
        #     print(f"{headers=}")
        #     print(f"{method=}")
        #     print(f"{path=}")
        #     print(f"{scheme=}")
        #     print(f"{authority=}")
        #     if authority:
        #         headers["host"] = authority

        #     request = Request(
        #         path, headers, "3", method, Transport(), app, b""
        #     )
        #     request.stream = Stream(
        #         connection=self._http, transmit=self.transmit
        #     )
        #     print(f"{request=}")

        #     asyncio.ensure_future(handler(request))

    async def send(self, data: bytes, end_stream: bool) -> None:
        print(f"[send]: {data=} {end_stream=}")
        print(self.response.headers)
        # self.connection.send_headers(
        #     stream_id=0,
        #     headers=[
        #         (b":status", str(self.response.status).encode()),
        #         *(
        #             (k.encode(), v.encode())
        #             for k, v in self.response.headers.items()
        #         ),
        #     ],
        # )
        # self.connection.send_data(
        #     stream_id=0,
        #     data=data,
        #     end_stream=end_stream,
        # )
        # self.transmit()

    def respond(self, response: BaseHTTPResponse) -> BaseHTTPResponse:
        print(f"[respond]: {response=}")
        self.response, response.stream = response, self
        return response


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


def get_config():
    config = QuicConfiguration(
        alpn_protocols=H3_ALPN + H0_ALPN + ["siduck"],
        is_client=False,
        max_datagram_frame_size=65536,
    )
    config.load_cert_chain("./cert.pem", "./key.pem", password="qqqqqqqq")
    return config


def get_ticket_store():
    return SessionTicketStore()
