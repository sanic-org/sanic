from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sanic.exceptions import RequestCancelled


if TYPE_CHECKING:
    from sanic.app import Sanic

import asyncio

from asyncio.transports import Transport
from time import monotonic as current_time

from sanic.log import error_logger
from sanic.models.server_types import ConnInfo, Signal


class SanicProtocol(asyncio.Protocol):
    __slots__ = (
        "app",
        # event loop, connection
        "loop",
        "transport",
        "connections",
        "conn_info",
        "signal",
        "_can_write",
        "_time",
        "_task",
        "_unix",
        "_data_received",
    )

    def __init__(
        self,
        *,
        loop,
        app: Sanic,
        signal=None,
        connections=None,
        unix=None,
        **kwargs,
    ):
        asyncio.set_event_loop(loop)
        self.loop = loop
        self.app: Sanic = app
        self.signal = signal or Signal()
        self.transport: Optional[Transport] = None
        self.connections = connections if connections is not None else set()
        self.conn_info: Optional[ConnInfo] = None
        self._can_write = asyncio.Event()
        self._can_write.set()
        self._unix = unix
        self._time = 0.0  # type: float
        self._task = None  # type: Optional[asyncio.Task]
        self._data_received = asyncio.Event()

    @property
    def ctx(self):
        if self.conn_info is not None:
            return self.conn_info.ctx
        else:
            return None

    async def send(self, data):
        """
        Generic data write implementation with backpressure control.
        """
        await self._can_write.wait()
        if self.transport.is_closing():
            raise RequestCancelled
        self.transport.write(data)
        self._time = current_time()

    async def receive_more(self):
        """
        Wait until more data is received into the Server protocol's buffer
        """
        self.transport.resume_reading()
        self._data_received.clear()
        await self._data_received.wait()

    def close(self, timeout: Optional[float] = None):
        """
        Attempt close the connection.
        """
        # Cause a call to connection_lost where further cleanup occurs
        if self.transport:
            self.transport.close()
            if timeout is None:
                timeout = self.app.config.GRACEFUL_SHUTDOWN_TIMEOUT
            self.loop.call_later(timeout, self.abort)

    def abort(self):
        """
        Force close the connection.
        """
        # Cause a call to connection_lost where further cleanup occurs
        if self.transport:
            self.transport.abort()
            self.transport = None

    # asyncio.Protocol API Callbacks #
    # ------------------------------ #
    def connection_made(self, transport):
        """
        Generic connection-made, with no connection_task, and no recv_buffer.
        Override this for protocol-specific connection implementations.
        """
        try:
            transport.set_write_buffer_limits(low=16384, high=65536)
            self.connections.add(self)
            self.transport = transport
            self.conn_info = ConnInfo(self.transport, unix=self._unix)
        except Exception:
            error_logger.exception("protocol.connect_made")

    def connection_lost(self, exc):
        try:
            self.connections.discard(self)
            self.resume_writing()
            self.conn_info.lost = True
            if self._task:
                self._task.cancel()
        except BaseException:
            error_logger.exception("protocol.connection_lost")

    def pause_writing(self):
        self._can_write.clear()

    def resume_writing(self):
        self._can_write.set()

    def data_received(self, data: bytes):
        try:
            self._time = current_time()
            if not data:
                return self.close()

            if self._data_received:
                self._data_received.set()
        except BaseException:
            error_logger.exception("protocol.data_received")
