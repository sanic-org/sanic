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
        if self.transport is None or self.transport.is_closing():
            # do not attempt to close again, already aborted or closing
            return

        # Check if write is already paused _before_ close() is called.
        write_was_paused = not self._can_write.is_set()
        # Trigger the UVLoop Stream Transport Close routine
        # Causes a call to connection_lost where further cleanup occurs
        # Close may fully close the connection now, but if there is still
        # data in the libuv buffer, then close becomes an async operation
        self.transport.close()
        try:
            # Check write-buffer data left _after_ close is called.
            # in UVLoop, get the data in the libuv transport write-buffer
            data_left = self.transport.get_write_buffer_size()
        # Some asyncio implementations don't support get_write_buffer_size
        except (AttributeError, NotImplementedError):
            data_left = 0
        if write_was_paused or data_left > 0:
            # don't call resume_writing here, it gets called by the transport
            # to unpause the protocol when it is ready for more data

            # Schedule the async close checker, to close the connection
            # after the transport is done, and clean everything up.
            if timeout is None:
                # This close timeout needs to be less than the graceful
                # shutdown timeout. The graceful shutdown _could_ be waiting
                # for this transport to close before shutting down the app.
                timeout = self.app.config.GRACEFUL_TCP_CLOSE_TIMEOUT
                # This is 5s by default.
        else:
            # Schedule the async close checker but with no timeout,
            # this will ensure abort() is called if required.
            if timeout is None:
                timeout = 0
        self.loop.call_soon(
            _async_protocol_transport_close,
            self,
            self.loop,
            timeout,
        )

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
        """
        This is a callback handler that is called from the asyncio
        transport layer implementation (eg, UVLoop's UVStreamTransport).
        It is scheduled to be called async after the transport has closed.
        When data is still in the send buffer, this call to connection_lost
        will be delayed until _after_ the buffer is finished being sent.

        So we can use this callback as a confirmation callback
        that the async write-buffer transfer is finished.
        """
        try:
            self.connections.discard(self)
            # unblock the send queue if it is paused,
            # this allows the route handler to see
            # the CancelledError exception
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


def _async_protocol_transport_close(
    protocol: SanicProtocol,
    loop: asyncio.AbstractEventLoop,
    timeout: float,
):
    """
    This function is scheduled to be called after close() is called.
    It checks that the transport has shut down properly, or waits
    for any remaining data to be sent, and aborts after a timeout.
    This is required if the transport is closed while there is an async
    large async transport write operation in progress.
    This is observed when NGINX reverse-proxy is the client.
    """
    if protocol.transport is None:
        # abort() is the only method that can make
        # protocol.transport be None, so abort was already called
        return
    # protocol.connection_lost does not set protocol.transport to None
    # so to detect it a different way with conninfo.lost
    elif protocol.conn_info is not None and protocol.conn_info.lost:
        # Terminus. Most connections finish the protocol here!
        # Connection_lost callback was executed already,
        # so transport did complete and close itself properly.
        # No need to call abort().

        # This is the last part of cleanup to do
        # that is not done by connection_lost handler.
        # Ensure transport is cleaned up by GC.
        protocol.transport = None
        return
    elif not protocol.transport.is_closing():
        raise RuntimeError(
            "You must call transport.close() before "
            "protocol._async_transport_close() runs."
        )

    write_is_paused = not protocol._can_write.is_set()
    try:
        # in UVLoop, get the data in the libuv write-buffer
        data_left = protocol.transport.get_write_buffer_size()
    # Some asyncio implementations don't support get_write_buffer_size
    except (AttributeError, NotImplementedError):
        data_left = 0
    if write_is_paused or data_left > 0:
        # don't need to call resume_writing here to unpause
        if timeout <= 0:
            # timeout is 0 or less, so we can simply abort now
            loop.call_soon(SanicProtocol.abort, protocol)
        else:
            next_check_interval = min(timeout, 0.1)
            next_check_timeout = timeout - next_check_interval
            loop.call_later(
                # Recurse back in after the timeout, to check again
                next_check_interval,
                # this next time with reduced timeout.
                _async_protocol_transport_close,
                protocol,
                loop,
                next_check_timeout,
            )
    else:
        # Not paused, and no data left in the buffer, but transport
        # is still open, connection_lost has not been called yet.
        # We can call abort() to fix that.
        loop.call_soon(SanicProtocol.abort, protocol)
