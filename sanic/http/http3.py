from __future__ import annotations

import asyncio

from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
    cast,
)

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
from aioquic.tls import SessionTicket

from sanic.compat import Header
from sanic.constants import LocalCertCreator
from sanic.exceptions import PayloadTooLarge, SanicException
from sanic.helpers import has_message_body
from sanic.http.stream import Stream
from sanic.http.tls.context import CertSelector, CertSimple, SanicSSLContext


if TYPE_CHECKING:  # noqa
    from sanic import Sanic
    from sanic.request import Request
    from sanic.response import BaseHTTPResponse
    from sanic.server.protocols.http_protocol import Http3Protocol

from sanic.http.constants import Stage
from sanic.log import Colors, logger


HttpConnection = Union[H0Connection, H3Connection]


class Transport:
    ...


class Receiver(ABC):
    future: asyncio.Future

    def __init__(self, transmit, protocol, request: Request) -> None:
        self.transmit = transmit
        self.protocol = protocol
        self.request = request

    @abstractmethod
    async def run(self):  # no cov
        ...


class HTTPReceiver(Receiver, Stream):
    stage: Stage

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.request_body = None
        self.stage = Stage.IDLE
        self.headers_sent = False
        self.response: Optional[BaseHTTPResponse] = None
        self.request_max_size = self.protocol.request_max_size
        self.request_bytes = 0

    async def run(self, exception: Optional[Exception] = None):
        self.stage = Stage.HANDLER
        self.head_only = self.request.method.upper() == "HEAD"

        if exception:
            logger.info(
                f"{Colors.BLUE}[exception]: "
                f"{Colors.RED}{exception}{Colors.END}",
                exc_info=True,
                extra={"verbosity": 1},
            )
            await self.error_response(exception)
        else:
            try:
                logger.info(
                    f"{Colors.BLUE}[request]:{Colors.END} {self.request}",
                    extra={"verbosity": 1},
                )
                await self.protocol.request_handler(self.request)
            except Exception as e:  # no cov
                # This should largely be handled within the request handler.
                # But, just in case...
                await self.run(e)
        self.stage = Stage.IDLE

    async def error_response(self, exception: Exception) -> None:
        """
        Handle response when exception encountered
        """
        # Disconnect after an error if in any other state than handler
        # if self.stage is not Stage.HANDLER:
        #     self.keep_alive = False

        # TODO:
        # - Do we need this?
        # Request failure? Respond but then disconnect
        if self.stage is Stage.REQUEST:
            self.stage = Stage.HANDLER

        # From request and handler states we can respond, otherwise be silent
        if self.stage is Stage.HANDLER:
            app = self.protocol.app

            # if self.request is None:
            #     self.create_empty_request()

            await app.handle_exception(self.request, exception)

    def _prepare_headers(
        self, response: BaseHTTPResponse
    ) -> List[Tuple[bytes, bytes]]:
        size = len(response.body) if response.body else 0
        headers = response.headers
        status = response.status

        if not has_message_body(status) and (
            size
            or "content-length" in headers
            or "transfer-encoding" in headers
        ):
            headers.pop("content-length", None)
            headers.pop("transfer-encoding", None)
            logger.warning(
                f"Message body set in response on {self.request.path}. "
                f"A {status} response may only have headers, no body."
            )
        elif "content-length" not in headers:
            if size:
                headers["content-length"] = size
            else:
                headers["transfer-encoding"] = "chunked"

        headers = [
            (b":status", str(response.status).encode()),
            *response.processed_headers,
        ]
        return headers

    def send_headers(self) -> None:
        logger.debug(
            f"{Colors.BLUE}[send]: {Colors.GREEN}HEADERS{Colors.END}",
            extra={"verbosity": 2},
        )
        if not self.response:
            raise Exception("no response")

        response = self.response
        headers = self._prepare_headers(response)

        self.protocol.connection.send_headers(
            stream_id=self.request.stream_id,
            headers=headers,
        )
        self.headers_sent = True
        self.stage = Stage.RESPONSE

        if self.response.body and not self.head_only:
            self._send(self.response.body, False)
        elif self.head_only:
            self.future.cancel()

    def respond(self, response: BaseHTTPResponse) -> BaseHTTPResponse:
        logger.debug(
            f"{Colors.BLUE}[respond]:{Colors.END} {response}",
            extra={"verbosity": 2},
        )

        if self.stage is not Stage.HANDLER:
            self.stage = Stage.FAILED
            raise RuntimeError("Response already started")

        # Disconnect any earlier but unused response object
        if self.response is not None:
            self.response.stream = None

        self.response, response.stream = response, self

        return response

    def receive_body(self, data: bytes) -> None:
        self.request_bytes += len(data)
        if self.request_bytes > self.request_max_size:
            raise PayloadTooLarge("Request body exceeds the size limit")

        self.request.body += data

    async def send(self, data: bytes, end_stream: bool) -> None:
        logger.debug(
            f"{Colors.BLUE}[send]: {Colors.GREEN}{data=} "
            f"{end_stream=}{Colors.END}",
            extra={"verbosity": 2},
        )
        self._send(data, end_stream)

    def _send(self, data: bytes, end_stream: bool) -> None:
        if not self.headers_sent:
            self.send_headers()
        if self.stage is not Stage.RESPONSE:
            raise Exception(f"not ready to send: {self.stage}")

        # Chunked
        if (
            self.response
            and self.response.headers.get("transfer-encoding") == "chunked"
        ):
            size = len(data)
            if end_stream:
                data = (
                    b"%x\r\n%b\r\n0\r\n\r\n" % (size, data)
                    if size
                    else b"0\r\n\r\n"
                )
            elif size:
                data = b"%x\r\n%b\r\n" % (size, data)

        logger.debug(
            f"{Colors.BLUE}[transmitting]{Colors.END}",
            extra={"verbosity": 2},
        )
        self.protocol.connection.send_data(
            stream_id=self.request.stream_id,
            data=data,
            end_stream=end_stream,
        )
        self.transmit()

        if end_stream:
            self.stage = Stage.IDLE


class WebsocketReceiver(Receiver):  # noqa
    async def run(self):
        ...


class WebTransportReceiver(Receiver):  # noqa
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
        self.protocol = protocol
        self.transmit = transmit
        self.receivers: Dict[int, Receiver] = {}

    def http_event_received(self, event: H3Event) -> None:
        logger.debug(
            f"{Colors.BLUE}[http_event_received]: "
            f"{Colors.YELLOW}{event}{Colors.END}",
            extra={"verbosity": 2},
        )
        receiver, created_new = self.get_or_make_receiver(event)
        receiver = cast(HTTPReceiver, receiver)

        if isinstance(event, HeadersReceived) and created_new:
            receiver.future = asyncio.ensure_future(receiver.run())
        elif isinstance(event, DataReceived):
            try:
                receiver.receive_body(event.data)
            except Exception as e:
                receiver.future.cancel()
                receiver.future = asyncio.ensure_future(receiver.run(e))
        else:
            logger.debug(
                f"{Colors.RED}DOING NOTHING{Colors.END}",
                extra={"verbosity": 2},
            )

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
        # TODO:
        # Cleanup
        # method_header, path_header, *rem = event.headers
        headers = Header(((k.decode(), v.decode()) for k, v in event.headers))
        # method = method_header[1].decode()
        # path = path_header[1]
        method = headers[":method"]
        path = headers[":path"].encode()
        scheme = headers.pop(":scheme", "")

        authority = headers.pop(":authority", "")

        if authority:
            headers["host"] = authority

        request = self.protocol.request_class(
            path, headers, "3", method, Transport(), self.protocol.app, b""
        )
        request._stream_id = event.stream_id
        request._scheme = scheme

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


def get_config(app: Sanic, ssl: Union[SanicSSLContext, CertSelector]):
    # TODO:
    # - proper selection needed if servince with multiple certs insted of
    #   just taking the first
    if isinstance(ssl, CertSelector):
        ssl = cast(SanicSSLContext, ssl.sanic_select[0])
    if not isinstance(ssl, CertSimple):
        raise SanicException("SSLContext is not CertSimple")

    config = QuicConfiguration(
        alpn_protocols=H3_ALPN + H0_ALPN + ["siduck"],
        is_client=False,
        max_datagram_frame_size=65536,
    )
    password = app.config.TLS_CERT_PASSWORD or None

    if app.config.LOCAL_CERT_CREATOR is LocalCertCreator.TRUSTME:
        raise SanicException(
            "Sorry, you cannot currently use trustme as a local certificate "
            "generator for an HTTP/3 server. This is not yet supported. You "
            "should be able to use mkcert instead. For more information, see: "
            "https://github.com/aiortc/aioquic/issues/295."
        )

    config.load_cert_chain(
        ssl.sanic["cert"], ssl.sanic["key"], password=password
    )

    return config
