from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sanic.http.constants import HTTP
from sanic.http.http3 import Http3
from sanic.touchup.meta import TouchUpMeta


if TYPE_CHECKING:
    from sanic.app import Sanic

import sys

from asyncio import CancelledError
from time import monotonic as current_time

from sanic.exceptions import (
    RequestCancelled,
    RequestTimeout,
    ServiceUnavailable,
)
from sanic.http import Http, Stage
from sanic.log import Colors, error_logger, logger
from sanic.models.server_types import ConnInfo
from sanic.request import Request
from sanic.server.protocols.base_protocol import SanicProtocol


ConnectionProtocol = type("ConnectionProtocol", (), {})
try:
    from aioquic.asyncio import QuicConnectionProtocol
    from aioquic.h3.connection import H3_ALPN, H3Connection
    from aioquic.quic.events import (
        DatagramFrameReceived,
        ProtocolNegotiated,
        QuicEvent,
    )

    ConnectionProtocol = QuicConnectionProtocol
except ModuleNotFoundError:  # no cov
    ...


class HttpProtocolMixin:
    __slots__ = ()
    __version__: HTTP

    def _setup_connection(self, *args, **kwargs):
        self._http = self.HTTP_CLASS(self, *args, **kwargs)
        self._time = current_time()
        try:
            self.check_timeouts()
        except AttributeError:
            ...

    def _setup(self):
        self.request: Optional[Request] = None
        self.access_log = self.app.config.ACCESS_LOG
        self.request_handler = self.app.handle_request
        self.error_handler = self.app.error_handler
        self.request_timeout = self.app.config.REQUEST_TIMEOUT
        self.response_timeout = self.app.config.RESPONSE_TIMEOUT
        self.keep_alive_timeout = self.app.config.KEEP_ALIVE_TIMEOUT
        self.request_max_size = self.app.config.REQUEST_MAX_SIZE
        self.request_class = self.app.request_class or Request

    @property
    def http(self):
        if not hasattr(self, "_http"):
            return None
        return self._http

    @property
    def version(self):
        return self.__class__.__version__


class HttpProtocol(HttpProtocolMixin, SanicProtocol, metaclass=TouchUpMeta):
    """
    This class provides implements the HTTP 1.1 protocol on top of our
    Sanic Server transport
    """

    HTTP_CLASS = Http

    __touchup__ = (
        "send",
        "connection_task",
    )
    __version__ = HTTP.VERSION_1
    __slots__ = (
        # request params
        "request",
        # request config
        "request_handler",
        "request_timeout",
        "response_timeout",
        "keep_alive_timeout",
        "request_max_size",
        "request_class",
        "error_handler",
        # enable or disable access log purpose
        "access_log",
        # connection management
        "state",
        "url",
        "_handler_task",
        "_http",
        "_exception",
        "recv_buffer",
    )

    def __init__(
        self,
        *,
        loop,
        app: Sanic,
        signal=None,
        connections=None,
        state=None,
        unix=None,
        **kwargs,
    ):
        super().__init__(
            loop=loop,
            app=app,
            signal=signal,
            connections=connections,
            unix=unix,
        )
        self.url = None
        self.state = state if state else {}
        self._setup()
        if "requests_count" not in self.state:
            self.state["requests_count"] = 0
        self._exception = None

    async def connection_task(self):  # no cov
        """
        Run a HTTP connection.

        Timeouts and some additional error handling occur here, while most of
        everything else happens in class Http or in code called from there.
        """
        try:
            self._setup_connection()
            await self.app.dispatch(
                "http.lifecycle.begin",
                inline=True,
                context={"conn_info": self.conn_info},
            )
            await self._http.http1()
        except CancelledError:
            pass
        except Exception:
            error_logger.exception("protocol.connection_task uncaught")
        finally:
            if (
                self.app.debug
                and self._http
                and self.transport
                and not self._http.upgrade_websocket
            ):
                ip = self.transport.get_extra_info("peername")
                error_logger.error(
                    "Connection lost before response written"
                    f" @ {ip} {self._http.request}"
                )
            self._http = None
            self._task = None
            try:
                self.close()
            except BaseException:
                error_logger.exception("Closing failed")
            finally:
                await self.app.dispatch(
                    "http.lifecycle.complete",
                    inline=True,
                    context={"conn_info": self.conn_info},
                )
                # Important to keep this Ellipsis here for the TouchUp module
                ...

    def check_timeouts(self):
        """
        Runs itself periodically to enforce any expired timeouts.
        """
        try:
            if not self._task:
                return
            duration = current_time() - self._time
            stage = self._http.stage
            if stage is Stage.IDLE and duration > self.keep_alive_timeout:
                logger.debug("KeepAlive Timeout. Closing connection.")
            elif stage is Stage.REQUEST and duration > self.request_timeout:
                logger.debug("Request Timeout. Closing connection.")
                self._http.exception = RequestTimeout("Request Timeout")
            elif stage is Stage.HANDLER and self._http.upgrade_websocket:
                logger.debug("Handling websocket. Timeouts disabled.")
                return
            elif (
                stage in (Stage.HANDLER, Stage.RESPONSE, Stage.FAILED)
                and duration > self.response_timeout
            ):
                logger.debug("Response Timeout. Closing connection.")
                self._http.exception = ServiceUnavailable("Response Timeout")
            else:
                interval = (
                    min(
                        self.keep_alive_timeout,
                        self.request_timeout,
                        self.response_timeout,
                    )
                    / 2
                )
                self.loop.call_later(max(0.1, interval), self.check_timeouts)
                return
            cancel_msg_args = ()
            if sys.version_info >= (3, 9):
                cancel_msg_args = ("Cancel connection task with a timeout",)
            self._task.cancel(*cancel_msg_args)
        except Exception:
            error_logger.exception("protocol.check_timeouts")

    async def send(self, data):  # no cov
        """
        Writes HTTP data with backpressure control.
        """
        await self._can_write.wait()
        if self.transport.is_closing():
            raise RequestCancelled
        await self.app.dispatch(
            "http.lifecycle.send",
            inline=True,
            context={"data": data},
        )
        self.transport.write(data)
        self._time = current_time()

    def close_if_idle(self) -> bool:
        """
        Close the connection if a request is not being sent or received

        :return: boolean - True if closed, false if staying open
        """
        if self._http is None or self._http.stage is Stage.IDLE:
            self.close()
            return True
        return False

    # -------------------------------------------- #
    # Only asyncio.Protocol callbacks below this
    # -------------------------------------------- #

    def connection_made(self, transport):
        """
        HTTP-protocol-specific new connection handler
        """
        try:
            # TODO: Benchmark to find suitable write buffer limits
            transport.set_write_buffer_limits(low=16384, high=65536)
            self.connections.add(self)
            self.transport = transport
            self._task = self.loop.create_task(self.connection_task())
            self.recv_buffer = bytearray()
            self.conn_info = ConnInfo(self.transport, unix=self._unix)
        except Exception:
            error_logger.exception("protocol.connect_made")

    def data_received(self, data: bytes):
        try:
            self._time = current_time()
            if not data:
                return self.close()
            self.recv_buffer += data

            if (
                len(self.recv_buffer) >= self.app.config.REQUEST_BUFFER_SIZE
                and self.transport
            ):
                self.transport.pause_reading()

            if self._data_received:
                self._data_received.set()
        except Exception:
            error_logger.exception("protocol.data_received")


class Http3Protocol(HttpProtocolMixin, ConnectionProtocol):  # type: ignore
    HTTP_CLASS = Http3
    __version__ = HTTP.VERSION_3

    def __init__(self, *args, app: Sanic, **kwargs) -> None:
        self.app = app
        super().__init__(*args, **kwargs)
        self._setup()
        self._connection: Optional[H3Connection] = None

    def quic_event_received(self, event: QuicEvent) -> None:
        logger.debug(
            f"{Colors.BLUE}[quic_event_received]: "
            f"{Colors.PURPLE}{event}{Colors.END}",
            extra={"verbosity": 2},
        )
        if isinstance(event, ProtocolNegotiated):
            self._setup_connection(transmit=self.transmit)
            if event.alpn_protocol in H3_ALPN:
                self._connection = H3Connection(
                    self._quic, enable_webtransport=True
                )
        elif isinstance(event, DatagramFrameReceived):
            if event.data == b"quack":
                self._quic.send_datagram_frame(b"quack-ack")

        #  pass event to the HTTP layer
        if self._connection is not None:
            for http_event in self._connection.handle_event(event):
                self._http.http_event_received(http_event)

    @property
    def connection(self) -> Optional[H3Connection]:
        return self._connection
