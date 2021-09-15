import asyncio
import random
import struct

from typing import (
    TYPE_CHECKING,
    AsyncIterator,
    Dict,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    Union,
)

from websockets.connection import CLOSED, CLOSING, OPEN, Event
from websockets.exceptions import ConnectionClosed, ConnectionClosedError
from websockets.frames import OP_PONG
from websockets.server import ServerConnection
from websockets.typing import Data

from sanic.log import error_logger
from sanic.server.protocols.base_protocol import SanicProtocol

from ...exceptions import ServerError
from .frame import WebsocketFrameAssembler


if TYPE_CHECKING:
    from websockets.frames import Frame


class WebsocketImplProtocol:
    connection: ServerConnection
    io_proto: Optional[SanicProtocol]
    loop: Optional[asyncio.BaseEventLoop]
    max_queue: int
    close_timeout: float
    ping_interval: Optional[float]
    ping_timeout: Optional[float]
    assembler: WebsocketFrameAssembler
    pings: Dict[bytes, asyncio.Future]  # Dict[bytes, asyncio.Future[None]]
    pings: Dict[bytes, asyncio.Future]  # Dict[bytes, asyncio.Future[None]]
    conn_mutex: asyncio.Lock
    recv_lock: asyncio.Lock
    process_event_mutex: asyncio.Lock
    can_pause: bool
    data_finished_fut: Optional[
        asyncio.Future
    ]  # Optional[asyncio.Future[None]]
    pause_frame_fut: Optional[asyncio.Future]  # Optional[asyncio.Future[None]]
    connection_lost_waiter: Optional[
        asyncio.Future
    ]  # Optional[asyncio.Future[None]]
    keepalive_ping_task: Optional[asyncio.Task]
    auto_closer_task: Optional[asyncio.Task]

    def __init__(
        self,
        connection,
        max_queue=None,
        ping_interval: Optional[float] = 20,
        ping_timeout: Optional[float] = 20,
        close_timeout: Optional[float] = 10,
        loop=None,
    ):
        self.connection = connection
        self.io_proto = None
        self.loop = None
        self.max_queue = max_queue
        self.close_timeout = close_timeout
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.assembler = WebsocketFrameAssembler(self)
        self.pings = {}
        self.conn_mutex = asyncio.Lock()
        self.recv_lock = asyncio.Lock()
        self.process_event_mutex = asyncio.Lock()
        self.data_finished_fut = None
        self.can_pause = True
        self.pause_frame_fut = None
        self.keepalive_ping_task = None
        self.auto_closer_task = None
        self.connection_lost_waiter = None

    @property
    def subprotocol(self):
        return self.connection.subprotocol

    def pause_frames(self):
        if not self.can_pause:
            return False
        if self.pause_frame_fut is not None:
            return False
        if self.loop is None or self.io_proto is None:
            return False
        if self.io_proto.transport is not None:
            self.io_proto.transport.pause_reading()
        self.pause_frame_fut = self.loop.create_future()
        return True

    def resume_frames(self):
        if self.pause_frame_fut is None:
            return False
        if self.loop is None or self.io_proto is None:
            error_logger.warning(
                "Websocket attempting to resume reading frames, but connection is gone."
            )
            return False
        if self.io_proto.transport is not None:
            self.io_proto.transport.resume_reading()
        self.pause_frame_fut.set_result(None)
        self.pause_frame_fut = None
        return True

    async def connection_made(self, io_proto: SanicProtocol, loop=None):
        if loop is None:
            try:
                loop = getattr(io_proto, "loop")
            except AttributeError:
                loop = asyncio.get_event_loop()
        self.loop = loop
        self.io_proto = io_proto  # this will be a WebSocketProtocol
        self.connection_lost_waiter = self.loop.create_future()
        self.data_finished_fut = asyncio.shield(self.loop.create_future())

        if self.ping_interval is not None:
            self.keepalive_ping_task = asyncio.create_task(
                self.keepalive_ping()
            )
        self.auto_closer_task = asyncio.create_task(
            self.auto_close_connection()
        )

    async def wait_for_connection_lost(self, timeout=None) -> bool:
        """
        Wait until the TCP connection is closed or ``timeout`` elapses.
        If timeout is None, wait forever.
        Recommend you should pass in self.close_timeout as timeout

        Return ``True`` if the connection is closed and ``False`` otherwise.

        """
        if self.connection_lost_waiter is None:
            return False
        if self.connection_lost_waiter.done():
            return True
        else:
            try:
                await asyncio.wait_for(
                    asyncio.shield(self.connection_lost_waiter), timeout
                )
                return True
            except asyncio.TimeoutError:
                # Re-check self.connection_lost_waiter.done() synchronously because
                # connection_lost() could run between the moment the timeout occurs
                # and the moment this coroutine resumes running.
                return self.connection_lost_waiter.done()

    async def process_events(self, events: Sequence[Event]) -> None:
        """
        Process a list of incoming events.
        """
        # Wrapped in a mutex lock, to prevent other incoming events
        # from processing at the same time
        async with self.process_event_mutex:
            for event in events:
                if event.opcode == OP_PONG:
                    await self.process_pong(event)
                else:
                    await self.assembler.put(event)

    async def process_pong(self, frame: "Frame") -> None:
        if frame.data in self.pings:
            # Acknowledge all pings up to the one matching this pong.
            ping_ids = []
            for ping_id, ping in self.pings.items():
                ping_ids.append(ping_id)
                if not ping.done():
                    ping.set_result(None)
                if ping_id == frame.data:
                    break
            else:  # noqa
                raise ServerError("ping_id is not in self.pings")
            # Remove acknowledged pings from self.pings.
            for ping_id in ping_ids:
                del self.pings[ping_id]

    async def keepalive_ping(self) -> None:
        """
        Send a Ping frame and wait for a Pong frame at regular intervals.
        This coroutine exits when the connection terminates and one of the
        following happens:
        - :meth:`ping` raises :exc:`ConnectionClosed`, or
        - :meth:`auto_close_connection` cancels :attr:`keepalive_ping_task`.
        """
        if self.ping_interval is None:
            return

        try:
            while True:
                await asyncio.sleep(self.ping_interval)

                # ping() raises CancelledError if the connection is closed,
                # when auto_close_connection() cancels self.keepalive_ping_task.

                # ping() raises ConnectionClosed if the connection is lost,
                # when connection_lost() calls abort_pings().

                ping_waiter = await self.ping()

                if self.ping_timeout is not None:
                    try:
                        await asyncio.wait_for(ping_waiter, self.ping_timeout)
                    except asyncio.TimeoutError:
                        error_logger.warning(
                            "Websocket timed out waiting for pong"
                        )
                        self.fail_connection(1011)
                        break
        except asyncio.CancelledError:
            raise
        except ConnectionClosed:
            pass
        except Exception:
            error_logger.warning("Unexpected exception in keepalive ping task")

    def fail_connection(self, code: int = 1006, reason: str = "") -> bool:
        """
        Fail the WebSocket Connection
        This requires:
        1. Stopping all processing of incoming data, which means cancelling
           pausing the underlying io protocol. The close code will be 1006
           unless a close frame was received earlier.
        2. Sending a close frame with an appropriate code if the opening
           handshake succeeded and the other side is likely to process it.
        3. Closing the connection. :meth:`auto_close_connection` takes care
           of this.
        (The specification describes these steps in the opposite order.)
        """
        if self.io_proto and self.io_proto.transport is not None:
            # Stop new data coming in
            # In Python Version 3.7: pause_reading is idempotent
            # i.e. it can be called when the transport is already paused or closed.
            self.io_proto.transport.pause_reading()

            # Keeping fail_connection() synchronous guarantees it can't
            # get stuck and simplifies the implementation of the callers.
            # Not draining the write buffer is acceptable in this context.

            # clear the send buffer
            _ = self.connection.data_to_send()
            # If we're not already CLOSED or CLOSING, then send the close.
            if self.connection.state is OPEN:
                if code in (1000, 1001):
                    self.connection.send_close(code, reason)
                else:
                    self.connection.fail_connection(code, reason)
                try:
                    data_to_send = self.connection.data_to_send()
                    while (
                        len(data_to_send)
                        and self.io_proto
                        and self.io_proto.transport is not None
                    ):
                        frame_data = data_to_send.pop(0)
                        self.io_proto.transport.write(frame_data)
                except Exception:
                    # sending close frames may fail if the
                    # transport closes during this period
                    ...
        if code == 1006:
            # Special case: 1006 consider the transport already closed
            self.connection.set_state(CLOSED)
        if (
            self.data_finished_fut is not None
            and not self.data_finished_fut.done()
        ):
            # We have a graceful auto-closer. Use it to close the connection.
            self.data_finished_fut.cancel()
            self.data_finished_fut = None
        if self.auto_closer_task is not None:
            if self.auto_closer_task.done():
                # auto_closer has already closed the connection?
                self.auto_closer_task = None
                return True
            return False
        else:
            # Auto closer is not running. Do it manually.
            if (
                self.loop is None
                or self.io_proto is None
                or self.io_proto.transport is None
            ):
                # We were never open, or already closed
                return True
            # cannot use the connection_lost_waiter future here,
            # because this is a synchronous function.
            self.io_proto.transport.close()
            self.loop.call_later(
                self.close_timeout, self.io_proto.transport.abort
            )

    async def auto_close_connection(self) -> None:
        """
        Close the WebSocket Connection
        When the opening handshake succeeds, :meth:`connection_open` starts
        this coroutine in a task. It waits for the data transfer phase to
        complete then it closes the TCP connection cleanly.
        When the opening handshake fails, :meth:`fail_connection` does the
        same. There's no data transfer phase in that case.
        """
        try:
            # Wait for the data transfer phase to complete.
            if self.data_finished_fut is not None:
                try:
                    await self.data_finished_fut
                except asyncio.CancelledError:
                    # Cancelled error will be called when data phase is cancelled
                    # This can be if an error occurred or the client app closed the connection
                    ...

            # Cancel the keepalive ping task.
            if self.keepalive_ping_task is not None:
                self.keepalive_ping_task.cancel()

            # Half-close the TCP connection if possible (when there's no TLS).
            if (
                self.io_proto
                and self.io_proto.transport is not None
                and self.io_proto.transport.can_write_eof()
            ):
                error_logger.warning("Websocket half-closing TCP connection")
                self.io_proto.transport.write_eof()
                if self.connection_lost_waiter is not None:
                    if await self.wait_for_connection_lost(timeout=0):
                        return
        except asyncio.CancelledError:
            ...
        finally:
            # The try/finally ensures that the transport never remains open,
            # even if this coroutine is cancelled (for example).
            self.auto_closer_task = None
            if self.io_proto is None or self.io_proto.transport is None:
                # we were never open, or already dead and buried. Can't do any finalization.
                return
            elif (
                self.connection_lost_waiter is not None
                and self.connection_lost_waiter.done()
            ):
                # connection was confirmed closed already, proceed to abort waiter
                ...
            elif self.io_proto.transport.is_closing():
                # Connection is already closing (due to half-close above)
                # proceed to abort waiter
                ...
            else:
                self.io_proto.transport.close()
            if self.connection_lost_waiter is None:
                # Our connection monitor task isn't running.
                try:
                    await asyncio.sleep(self.close_timeout)
                except asyncio.CancelledError:
                    ...
                if self.io_proto and self.io_proto.transport is not None:
                    self.io_proto.transport.abort()
            else:
                if await self.wait_for_connection_lost(
                    timeout=self.close_timeout
                ):
                    # Connection aborted before the timeout expired.
                    return
                error_logger.warning(
                    "Timeout waiting for TCP connection to close. Aborting"
                )
                if self.io_proto and self.io_proto.transport is not None:
                    self.io_proto.transport.abort()

    def abort_pings(self) -> None:
        """
        Raise ConnectionClosed in pending keepalive pings.
        They'll never receive a pong once the connection is closed.
        """
        if self.connection.state is not CLOSED:
            raise ServerError(
                "webscoket about_pings should only be called after connection state is changed to CLOSED"
            )

        for ping in self.pings.values():
            ping.set_exception(ConnectionClosedError(1006, ""))
            # If the exception is never retrieved, it will be logged when ping
            # is garbage-collected. This is confusing for users.
            # Given that ping is done (with an exception), canceling it does
            # nothing, but it prevents logging the exception.
            ping.cancel()

    async def close(self, code: int = 1000, reason: str = "") -> None:
        """
        Perform the closing handshake.
        :meth:`close` waits for the other end to complete the handshake and
        for the TCP connection to terminate.
        :meth:`close` is idempotent: it doesn't do anything once the
        connection is closed.
        :param code: WebSocket close code
        :param reason: WebSocket close reason
        """
        async with self.conn_mutex:
            if self.connection.state is OPEN:
                self.connection.send_close(code, reason)
                data_to_send = self.connection.data_to_send()
                await self.send_data(data_to_send)

    async def recv(self, timeout: Optional[float] = None) -> Optional[Data]:
        """
        Receive the next message.
        Return a :class:`str` for a text frame and :class:`bytes` for a binary
        frame.
        When the end of the message stream is reached, :meth:`recv` raises
        :exc:`~websockets.exceptions.ConnectionClosed`. Specifically, it
        raises :exc:`~websockets.exceptions.ConnectionClosedOK` after a normal
        connection closure and
        :exc:`~websockets.exceptions.ConnectionClosedError` after a protocol
        error or a network failure.
        If ``timeout`` is ``None``, block until a message is received. Else,
        if no message is received within ``timeout`` seconds, return ``None``.
        Set ``timeout`` to ``0`` to check if a message was already received.
        :raises ~websockets.exceptions.ConnectionClosed: when the
            connection is closed
        :raises ServerError: if two tasks call :meth:`recv` or
            :meth:`recv_streaming` concurrently
        """

        if self.recv_lock.locked():
            raise ServerError(
                "cannot call recv while another task is already waiting for the next message"
            )
        await self.recv_lock.acquire()
        if self.connection.state in (CLOSED, CLOSING):
            raise ServerError(
                "Cannot receive from websocket interface after it is closed."
            )
        try:
            return await self.assembler.get(timeout)
        finally:
            self.recv_lock.release()

    async def recv_burst(self, max_recv=256) -> Sequence[Data]:
        """
        Receive the messages which have arrived since last checking.
        Return a :class:`list` containing :class:`str` for a text frame
        and :class:`bytes` for a binary frame.
        When the end of the message stream is reached, :meth:`recv_burst`
        raises :exc:`~websockets.exceptions.ConnectionClosed`. Specifically,
        it raises :exc:`~websockets.exceptions.ConnectionClosedOK` after a
        normal connection closure and
        :exc:`~websockets.exceptions.ConnectionClosedError` after a protocol
        error or a network failure.
        :raises ~websockets.exceptions.ConnectionClosed: when the
            connection is closed
        :raises ServerError: if two tasks call :meth:`recv_burst` or
            :meth:`recv_streaming` concurrently
        """

        if self.recv_lock.locked():
            raise ServerError(
                "cannot call recv_burst while another task is already waiting for the next message"
            )
        await self.recv_lock.acquire()
        if self.connection.state in (CLOSED, CLOSING):
            raise ServerError(
                "Cannot receive from websocket interface after it is closed."
            )
        messages = []
        try:
            # Prevent pausing the transport when we're
            # receiving a burst of messages
            self.can_pause = False
            while True:
                m = await self.assembler.get(timeout=0)
                if m is None:
                    # None left in the burst. This is good!
                    break
                messages.append(m)
                if len(messages) >= max_recv:
                    # Too much data in the pipe. Hit our burst limit.
                    break
                # Allow an eventloop iteration for the
                # next message to pass into the Assembler
                await asyncio.sleep(0)
        finally:
            self.can_pause = True
            self.recv_lock.release()
        return messages

    async def recv_streaming(self) -> AsyncIterator[Data]:
        """
        Receive the next message frame by frame.
        Return an iterator of :class:`str` for a text frame and :class:`bytes`
        for a binary frame. The iterator should be exhausted, or else the
        connection will become unusable.
        With the exception of the return value, :meth:`recv_streaming` behaves
        like :meth:`recv`.
        """
        if self.recv_lock.locked():
            raise ServerError(
                "cannot call recv_streaming while another task is already waiting for the next message"
            )
        await self.recv_lock.acquire()
        if self.connection.state in (CLOSED, CLOSING):
            raise ServerError(
                "Cannot receive from websocket interface after it is closed."
            )
        try:
            self.can_pause = False
            async for m in self.assembler.get_iter():
                yield m
        finally:
            self.can_pause = True
            self.recv_lock.release()

    async def send(self, message: Union[Data, Iterable[Data]]) -> None:
        """
        Send a message.
        A string (:class:`str`) is sent as a `Text frame`_. A bytestring or
        bytes-like object (:class:`bytes`, :class:`bytearray`, or
        :class:`memoryview`) is sent as a `Binary frame`_.
        .. _Text frame: https://tools.ietf.org/html/rfc6455#section-5.6
        .. _Binary frame: https://tools.ietf.org/html/rfc6455#section-5.6
        :meth:`send` also accepts an iterable of strings, bytestrings, or
        bytes-like objects. In that case the message is fragmented. Each item
        is treated as a message fragment and sent in its own frame. All items
        must be of the same type, or else :meth:`send` will raise a
        :exc:`TypeError` and the connection will be closed.
        :meth:`send` rejects dict-like objects because this is often an error.
        If you wish to send the keys of a dict-like object as fragments, call
        its :meth:`~dict.keys` method and pass the result to :meth:`send`.
        :raises TypeError: for unsupported inputs
        """
        async with self.conn_mutex:

            if self.connection.state in (CLOSED, CLOSING):
                raise ServerError(
                    "Cannot write to websocket interface after it is closed."
                )
            if (
                self.data_finished_fut is None
                or self.data_finished_fut.cancelled()
                or self.data_finished_fut.done()
            ):
                raise ServerError(
                    "Cannot write to websocket interface after it is finished."
                )

            # Unfragmented message -- this case must be handled first because
            # strings and bytes-like objects are iterable.

            if isinstance(message, str):
                self.connection.send_text(message.encode("utf-8"))
                await self.send_data(self.connection.data_to_send())

            elif isinstance(message, (bytes, bytearray, memoryview)):
                self.connection.send_binary(message)
                await self.send_data(self.connection.data_to_send())

            elif isinstance(message, Mapping):
                # Catch a common mistake -- passing a dict to send().
                raise TypeError("data is a dict-like object")

            elif isinstance(message, Iterable):
                # Fragmented message -- regular iterator.
                raise NotImplementedError(
                    "Fragmented websocket messages are not supported."
                )
            else:
                raise TypeError("Websocket data must be bytes, str.")

    async def ping(self, data: Optional[Data] = None) -> asyncio.Future:
        """
        Send a ping.
        Return an :class:`~asyncio.Future` that will be resolved when the
        corresponding pong is received. You can ignore it if you don't intend
        to wait.
        A ping may serve as a keepalive or as a check that the remote endpoint
        received all messages up to this point::
            await pong_event = ws.ping()
            await pong_event # only if you want to wait for the pong
        By default, the ping contains four random bytes. This payload may be
        overridden with the optional ``data`` argument which must be a string
        (which will be encoded to UTF-8) or a bytes-like object.
        """
        async with self.conn_mutex:
            if self.connection.state in (CLOSED, CLOSING):
                raise ServerError(
                    "Cannot send a ping when the websocket interface is closed."
                )
            if data is not None:
                if isinstance(data, str):
                    data = data.encode("utf-8")
                elif isinstance(data, (bytearray, memoryview)):
                    data = bytes(data)

            # Protect against duplicates if a payload is explicitly set.
            if data in self.pings:
                raise ValueError(
                    "already waiting for a pong with the same data"
                )

            # Generate a unique random payload otherwise.
            while data is None or data in self.pings:
                data = struct.pack("!I", random.getrandbits(32))

            self.pings[data] = self.io_proto.loop.create_future()

            self.connection.send_ping(data)
            await self.send_data(self.connection.data_to_send())

            return asyncio.shield(self.pings[data])

    async def pong(self, data: Data = b"") -> None:
        """
        Send a pong.
        An unsolicited pong may serve as a unidirectional heartbeat.
        The payload may be set with the optional ``data`` argument which must
        be a string (which will be encoded to UTF-8) or a bytes-like object.
        """
        async with self.conn_mutex:
            if self.connection.state in (CLOSED, CLOSING):
                # Cannot send pong after transport is shutting down
                return
            if isinstance(data, str):
                data = data.encode("utf-8")
            elif isinstance(data, (bytearray, memoryview)):
                data = bytes(data)
            self.connection.send_pong(data)
            await self.send_data(self.connection.data_to_send())

    async def send_data(self, data_to_send):
        for data in data_to_send:
            if data:
                await self.io_proto.send(data)
            else:
                # Send an EOF
                # We don't actually send it, just trigger to autoclose the connection
                if (
                    self.auto_closer_task is not None
                    and not self.auto_closer_task.done()
                    and self.data_finished_fut is not None
                    and not self.data_finished_fut.done()
                ):
                    # Auto-close the connection
                    self.data_finished_fut.set_result(None)
                else:
                    # This will fail the connection appropriately
                    SanicProtocol.close(self.io_proto, timeout=1.0)

    async def async_data_received(self, data_to_send, events_to_process):
        if self.connection.state == OPEN and len(data_to_send) > 0:
            # receiving data can generate data to send (eg, pong for a ping)
            # send connection.data_to_send()
            await self.send_data(data_to_send)
        if len(events_to_process) > 0:
            await self.process_events(events_to_process)

    def data_received(self, data):
        self.connection.receive_data(data)
        data_to_send = self.connection.data_to_send()
        events_to_process = self.connection.events_received()
        if len(data_to_send) > 0 or len(events_to_process) > 0:
            asyncio.create_task(
                self.async_data_received(data_to_send, events_to_process)
            )

    async def async_eof_received(self, data_to_send, events_to_process):
        # receiving EOF can generate data to send
        # send connection.data_to_send()
        if self.connection.state == OPEN:
            await self.send_data(data_to_send)
        if len(events_to_process) > 0:
            await self.process_events(events_to_process)

        if (
            self.auto_closer_task is not None
            and not self.auto_closer_task.done()
            and self.data_finished_fut is not None
            and not self.data_finished_fut.done()
        ):
            # Auto-close the connection
            self.data_finished_fut.set_result(None)
        else:
            # This will fail the connection appropriately
            SanicProtocol.close(self.io_proto, timeout=1.0)

    def eof_received(self) -> Optional[bool]:
        self.connection.receive_eof()
        data_to_send = self.connection.data_to_send()
        events_to_process = self.connection.events_received()
        if len(data_to_send) > 0 or len(events_to_process) > 0:
            asyncio.create_task(
                self.async_eof_received(data_to_send, events_to_process)
            )
        return False

    def connection_lost(self, exc):
        """
        The WebSocket Connection is Closed.
        """
        self.connection.set_state(CLOSED)
        self.abort_pings()
        if self.connection_lost_waiter is not None:
            self.connection_lost_waiter.set_result(None)
