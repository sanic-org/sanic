import random
import struct
from email.utils import formatdate
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    MutableMapping,
    Optional,
    Union,
    Iterable,
    Sequence,
    Mapping, AsyncIterator
)
import codecs

from httptools import HttpParserUpgrade  # type: ignore
from websockets.server import ServerConnection
from websockets.connection import Event, OPEN, CLOSING, CLOSED
from websockets.exceptions import ConnectionClosed, InvalidHandshake, InvalidOrigin, InvalidUpgrade, \
    ConnectionClosedError
from websockets.typing import Data
from websockets.frames import Frame, Opcode, prepare_ctrl, OP_PONG
from websockets.utils import accept_key

from sanic.exceptions import InvalidUsage, Forbidden, SanicException
from sanic.server import HttpProtocol, SanicProtocol
from sanic.log import error_logger, logger

import asyncio


ASIMessage = MutableMapping[str, Any]
UTF8Decoder = codecs.getincrementaldecoder("utf-8")

class WebsocketFrameAssembler:
    """
    Assemble a message from frames.
    Code borrowed from aaugustin/websockets project:
    https://github.com/aaugustin/websockets/blob/6eb98dd8fa5b2c896b9f6be7e8d117708da82a39/src/websockets/sync/messages.py
    """
    __slots__ = ("protocol", "read_mutex", "write_mutex", "message_complete", "message_fetched", "get_in_progress", "decoder", "completed_queue", "chunks", "chunks_queue", "paused", "get_id", "put_id")

    def __init__(self, protocol) -> None:

        self.protocol = protocol

        self.read_mutex = asyncio.Lock()
        self.write_mutex = asyncio.Lock()

        self.completed_queue = asyncio.Queue(maxsize=1)  # type: asyncio.Queue[Data]


        # put() sets this event to tell get() that a message can be fetched.
        self.message_complete = asyncio.Event()
        # get() sets this event to let put()
        self.message_fetched = asyncio.Event()

        # This flag prevents concurrent calls to get() by user code.
        self.get_in_progress = False

        # Decoder for text frames, None for binary frames.
        self.decoder: Optional[codecs.IncrementalDecoder] = None

        # Buffer data from frames belonging to the same message.
        self.chunks: List[Data] = []

        # When switching from "buffering" to "streaming", we use a thread-safe
        # queue for transferring frames from the writing thread (library code)
        # to the reading thread (user code). We're buffering when chunks_queue
        # is None and streaming when it's a Queue. None is a sentinel
        # value marking the end of the stream, superseding message_complete.

        # Stream data from frames belonging to the same message.
        self.chunks_queue: Optional[asyncio.Queue[Optional[Data]]] = None

        # Flag to indicate we've paused the protocol
        self.paused = False


    async def get(self, timeout: Optional[float] = None) -> Optional[Data]:
        """
        Read the next message.
        :meth:`get` returns a single :class:`str` or :class:`bytes`.
        If the :message was fragmented, :meth:`get` waits until the last frame
        is received, then it reassembles the message.
        If ``timeout`` is set and elapses before a complete message is
        received, :meth:`get` returns ``None``.
        """
        async with self.read_mutex:
            if timeout is not None and timeout <= 0:
                if not self.message_complete.is_set():
                    return None
            assert not self.get_in_progress
            self.get_in_progress = True

            # If the message_complete event isn't set yet, release the lock to
            # allow put() to run and eventually set it.
            # Locking with get_in_progress ensures only one thread can get here.
            if timeout is None:
                completed = await self.message_complete.wait()
            elif timeout <= 0:
                completed = self.message_complete.is_set()
            else:
                completed = await asyncio.wait_for(self.message_complete.wait(), timeout=timeout)

            # Unpause the transport, if its paused
            if self.paused:
                self.protocol.resume_frames()
                self.paused = False
            assert self.get_in_progress
            self.get_in_progress = False

            # Waiting for a complete message timed out.
            if not completed:
                return None

            assert self.message_complete.is_set()
            self.message_complete.clear()

            joiner: Data = b"" if self.decoder is None else ""
            # mypy cannot figure out that chunks have the proper type.
            message: Data = joiner.join(self.chunks)  # type: ignore

            assert not self.message_fetched.is_set()
            self.message_fetched.set()
            self.chunks = []
            assert self.chunks_queue is None

            return message

    async def get_iter(self) -> AsyncIterator[Data]:
        """
        Stream the next message.
        Iterating the return value of :meth:`get_iter` yields a :class:`str`
        or :class:`bytes` for each frame in the message.
        """
        async with self.read_mutex:
            assert not self.get_in_progress
            self.get_in_progress = True

            chunks = self.chunks
            self.chunks = []
            self.chunks_queue = asyncio.Queue()

            # Sending None in chunk_queue supersedes setting message_complete
            # when switching to "streaming". If message is already complete
            # when the switch happens, put() didn't send None, so we have to.
            if self.message_complete.is_set():
                await self.chunks_queue.put(None)

            # Locking with get_in_progress ensures only one thread can get here.
            for c in chunks:
                yield c
            while True:
                chunk = await self.chunks_queue.get()
                if chunk is None:
                    break
                yield chunk

            # Unpause the transport, if its paused
            if self.paused:
                self.protocol.resume_frames()
                self.paused = False
            assert self.get_in_progress
            self.get_in_progress = False
            assert self.message_complete.is_set()
            self.message_complete.clear()

            assert not self.message_fetched.is_set()

            self.message_fetched.set()

            assert self.chunks == []
            self.chunks_queue = None

    async def put(self, frame: Frame) -> None:
        """
        Add ``frame`` to the next message.
        When ``frame`` is the final frame in a message, :meth:`put` waits
        until the message is fetched, either by calling :meth:`get` or by
        iterating the return value of :meth:`get_iter`.
        :meth:`put` assumes that the stream of frames respects the protocol.
        If it doesn't, the behavior is undefined.
        """
        id = self.put_id
        self.put_id += 1
        async with self.write_mutex:
            if frame.opcode is Opcode.TEXT:
                self.decoder = UTF8Decoder(errors="strict")
            elif frame.opcode is Opcode.BINARY:
                self.decoder = None
            elif frame.opcode is Opcode.CONT:
                pass
            else:
                # Ignore control frames.
                return
            data: Data
            if self.decoder is not None:
                data = self.decoder.decode(frame.data, frame.fin)
            else:
                data = frame.data
            if self.chunks_queue is None:
                self.chunks.append(data)
            else:
                await self.chunks_queue.put(data)

            if not frame.fin:
                return
            if not self.get_in_progress:
                self.paused = self.protocol.pause_frames()
            # Message is complete. Wait until it's fetched to return.

            if self.chunks_queue is not None:
                await self.chunks_queue.put(None)

            assert not self.message_complete.is_set()
            self.message_complete.set()
            assert not self.message_fetched.is_set()

            # Release the lock to allow get() to run and eventually set the event.
            await self.message_fetched.wait()
            assert self.message_fetched.is_set()
            self.message_fetched.clear()
            self.decoder = None

class WebsocketImplProtocol:
    def __init__(self, connection, max_queue=None, ping_interval: Optional[float] = 20, ping_timeout: Optional[float] = 20, loop=None):
        self.connection = connection  # type: ServerConnection
        self.io_proto = None  # type: Optional[SanicProtocol]
        self.loop = None  # type: Optional[asyncio.BaseEventLoop]
        self.max_queue = max_queue
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.assembler = WebsocketFrameAssembler(self)
        self.pings: Dict[bytes, asyncio.Future[None]] = {}
        self.conn_mutex = asyncio.Lock()
        self.recv_lock = asyncio.Lock()
        self.process_event_mutex = asyncio.Lock()
        self.data_finished_fut = None  # type: Optional[asyncio.Future[None]]
        self.can_pause = True
        self.pause_frame_fut = None  # type: Optional[asyncio.Future[None]]
        self.keepalive_ping_task = None
        self.close_connection_task = None
        self.connection_lost_waiter = None  # type: Optional[asyncio.Future[None]]

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
            error_logger.warning("Websocket attempting to resume reading frames, but connection is gone.")
            return False
        if self.io_proto.transport is not None:
            self.io_proto.transport.resume_reading()
        self.pause_frame_fut.set_result(None)
        self.pause_frame_fut = None
        return True

    async def connection_made(self, io_proto: asyncio.Protocol, loop=None):
        if loop is None:
            try:
                loop = getattr(io_proto, "loop")
            except AttributeError:
                loop = asyncio.get_event_loop()
        self.loop = loop
        self.io_proto: WebSocketProtocol = io_proto
        self.connection_lost_waiter = self.loop.create_future()
        self.data_finished_fut = asyncio.shield(self.loop.create_future())

        if self.ping_interval is not None:
            self.keepalive_ping_task = asyncio.create_task(self.keepalive_ping())
        self.close_connection_task = asyncio.create_task(self.auto_close_connection())

    async def wait_for_connection_lost(self, timeout=10) -> bool:
        """
        Wait until the TCP connection is closed or ``timeout`` elapses.

        Return ``True`` if the connection is closed and ``False`` otherwise.

        """
        if self.connection_lost_waiter is None:
            return False
        if not self.connection_lost_waiter.done():
            try:
                await asyncio.wait_for(
                    asyncio.shield(self.connection_lost_waiter), timeout
                )
            except asyncio.TimeoutError:
                pass
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

    async def process_pong(self, frame: Frame) -> None:
        if frame.data in self.pings:
            # Acknowledge all pings up to the one matching this pong.
            ping_id = None
            ping_ids = []
            for ping_id, ping in self.pings.items():
                ping_ids.append(ping_id)
                if not ping.done():
                    ping.set_result(None)
                if ping_id == frame.data:
                    break
            else:  # pragma: no cover
                assert False, "ping_id is in self.pings"
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
                        error_logger.warning("Websocket timed out waiting for pong")
                        self.fail_connection(1011)
                        break
        except asyncio.CancelledError:
            raise
        except ConnectionClosed:
            pass
        except BaseException:
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
        if self.io_proto.transport is not None:
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
                self.connection.fail_connection(code, reason)
                for frame_data in self.connection.data_to_send():
                    self.io_proto.transport.write(frame_data)
        if self.close_connection_task is not None and not self.close_connection_task.done():
            if self.data_finished_fut is not None and not self.data_finished_fut.done():
                self.data_finished_fut.cancel()
            # Don't close, auto_close_connection will take care of it.
            return False
        SanicProtocol.close(self.io_proto)
        return True

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
                    pass

            # Cancel the keepalive ping task.
            if self.keepalive_ping_task is not None:
                self.keepalive_ping_task.cancel()

            # Half-close the TCP connection if possible (when there's no TLS).
            if self.io_proto.transport is not None and self.io_proto.transport.can_write_eof():
                error_logger.warning("Websocket half-closing TCP connection")
                self.io_proto.transport.write_eof()
                if self.connection_lost_waiter is not None:
                    if await self.wait_for_connection_lost(timeout=0):
                        return
        finally:
            # The try/finally ensures that the transport never remains open,
            # even if this coroutine is cancelled (for example).
            if self.connection_lost_waiter is not None and self.connection_lost_waiter.done():
                if self.io_proto.transport is None or self.io_proto.transport.is_closing():
                    return
            SanicProtocol.close(self.io_proto)
            if self.connection_lost_waiter is not None:
                await self.wait_for_connection_lost()
                if self.connection_lost_waiter.done():
                    return
                error_logger.warning("Timeout waiting for TCP connection to close. Aborting")
                if self.io_proto.transport is not None:
                    self.io_proto.transport.abort()

    def abort_pings(self) -> None:
        """
        Raise ConnectionClosed in pending keepalive pings.
        They'll never receive a pong once the connection is closed.
        """
        assert self.connection.state is CLOSED

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
        :raises RuntimeError: if two tasks call :meth:`recv` or
            :meth:`recv_streaming` concurrently
        """

        # TODO HANDLE THE SITUATION WHERE THE CONNECTION IS CLOSED

        if self.recv_lock.locked():
            raise RuntimeError(
                "cannot call recv while another task "
                "is already waiting for the next message"
            )
        await self.recv_lock.acquire()
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
        :raises RuntimeError: if two threads call :meth:`recv` or
            :meth:`recv_streaming` concurrently
        """

        # TODO HANDLE THE SITUATION WHERE THE CONNECTION IS CLOSED

        if self.recv_lock.locked():
            raise RuntimeError(
                "cannot call recv_burst while another task "
                "is already waiting for the next message"
            )
        await self.recv_lock.acquire()

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
            raise RuntimeError(
                "cannot call recv_streaming while another task "
                "is already waiting for the next message"
            )
        await self.recv_lock.acquire()
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

            # TODO HANDLE THE SITUATION WHERE THE CONNECTION IS CLOSED

            # Unfragmented message -- this case must be handled first because
            # strings and bytes-like objects are iterable.

            if isinstance(message, str):
                self.connection.send_text(message.encode("utf-8"))
                await self.send_data(self.connection.data_to_send())

            elif isinstance(message, (bytes, bytearray, memoryview)):
                self.connection.send_binary(message)
                await self.send_data(self.connection.data_to_send())

            # Catch a common mistake -- passing a dict to send().

            elif isinstance(message, Mapping):
                raise TypeError("data is a dict-like object")

            # Fragmented message -- regular iterator.

            elif isinstance(message, Iterable):
                # TODO use an incremental encoder maybe?
                raise NotImplementedError

            else:
                raise TypeError("data must be bytes, str, or iterable")

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

            # TODO HANDLE THE SITUATION WHERE THE CONNECTION IS CLOSED

            if data is not None:
                data = prepare_ctrl(data)

            # Protect against duplicates if a payload is explicitly set.
            if data in self.pings:
                raise ValueError("already waiting for a pong with the same data")

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
            # TODO HANDLE THE SITUATION WHERE THE CONNECTION IS CLOSED

            data = prepare_ctrl(data)

            self.connection.send_pong(data)
            await self.send_data(self.connection.data_to_send())

    async def send_data(self, data_to_send):
        for data in data_to_send:
            if data:
                await self.io_proto.send(data)
            else:
                # Send an EOF
                # We don't actually send it, just close the connection
                if self.close_connection_task is not None and not self.close_connection_task.done() and \
                        self.data_finished_fut is not None and not self.data_finished_fut.done():
                    # Auto-close the connection
                    self.data_finished_fut.set_result(None)
                else:
                    # This will fail the connection appropriately
                    self.io_proto.close()

    async def async_data_received(self, data_to_send, events_to_process):
        if len(data_to_send) > 0:
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
            asyncio.create_task(self.async_data_received(data_to_send, events_to_process))

    async def async_eof_received(self, data_to_send, events_to_process):
        # receiving EOF can generate data to send
        # send connection.data_to_send()
        await self.send_data(data_to_send)
        if len(events_to_process) > 0:
            await self.process_events(events_to_process)

        if self.close_connection_task is not None and not self.close_connection_task.done() and \
                self.data_finished_fut is not None and not self.data_finished_fut.done():
            # Auto-close the connection
            self.data_finished_fut.set_result(None)
        else:
            # This will fail the connection appropriately
            self.io_proto.close()

    def eof_received(self) -> Optional[bool]:
        self.connection.receive_eof()
        data_to_send = self.connection.data_to_send()
        events_to_process = self.connection.events_received()
        if len(data_to_send) > 0 or len(events_to_process) > 0:
            asyncio.create_task(self.async_eof_received(data_to_send, events_to_process))
        return False

    def connection_lost(self, exc):
        """
        The WebSocket Connection is Closed.
        """
        self.connection.set_state(CLOSED)
        self.abort_pings()
        if self.connection_lost_waiter is not None:
            self.connection_lost_waiter.set_result(None)


class WebSocketProtocol(HttpProtocol):
    def __init__(
        self,
        *args,
        websocket_timeout=10,
        websocket_max_size=None,
        websocket_max_queue=None,
        websocket_read_limit=2 ** 16,
        websocket_write_limit=2 ** 16,
        websocket_ping_interval=20,
        websocket_ping_timeout=20,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.websocket = None # type: Union[None, WebsocketImplProtocol]
        # self.app = None
        self.websocket_timeout = websocket_timeout
        self.websocket_max_size = websocket_max_size
        if websocket_max_queue is not None and int(websocket_max_queue) > 0:
            error_logger.warning(DeprecationWarning("websocket_max_queue is no longer used. No websocket message queueing is implemented."))
        self.websocket_read_limit = websocket_read_limit
        self.websocket_write_limit = websocket_write_limit
        self.websocket_ping_interval = websocket_ping_interval
        self.websocket_ping_timeout = websocket_ping_timeout

    # timeouts make no sense for websocket routes
    def request_timeout_callback(self):
        if self.websocket is None:
            super().request_timeout_callback()

    def response_timeout_callback(self):
        if self.websocket is None:
            super().response_timeout_callback()

    def keep_alive_timeout_callback(self):
        if self.websocket is None:
            super().keep_alive_timeout_callback()

    def connection_lost(self, exc):
        if self.websocket is not None:
            self.websocket.connection_lost(exc)
        super().connection_lost(exc)

    def data_received(self, data):
        if self.websocket is not None:
            self.websocket.data_received(data)
        else:
            # Pass it to HttpProtocol handler first
            # That will (hopefully) upgrade it to a websocket.
            super().data_received(data)

    def eof_received(self) -> Optional[bool]:
        if self.websocket is not None:
            return self.websocket.eof_received()
        else:
            return False

    def close(self):
        # Called by HttpProtocol at the end of connection_task
        # If we've upgraded to websocket, we do our own closure
        if self.websocket is not None:
            self.websocket.fail_connection(1001)
        else:
            super().close()

    def close_if_idle(self):
        # Called by Sanic Server when shutting down
        # If we've upgraded to websocket, shut it down
        if self.websocket is not None:
            if self.websocket.connection.state in (CLOSING, CLOSED):
                return True
            else:
                return self.websocket.fail_connection(1001)
        else:
            return super().close_if_idle()

    async def websocket_handshake(self, request, subprotocols=Optional[Sequence[str]]):
        # let the websockets package do the handshake with the client
        headers = {"Upgrade": "websocket", "Connection": "Upgrade"}
        try:
            if subprotocols is not None:
                # subprotocols can be a set or frozenset, but ServerConnection needs a list
                subprotocols = list(subprotocols)
            ws_server = ServerConnection(max_size=self.websocket_max_size, subprotocols=subprotocols,
                                         state=OPEN, logger=error_logger)
            key, extensions_header, protocol_header = ws_server.process_request(request)
        except InvalidOrigin as exc:
            raise Forbidden(
                f"Failed to open a WebSocket connection: {exc}.\n",
            )
        except InvalidUpgrade as exc:
            msg = (
                    f"Failed to open a WebSocket connection: {exc}.\n"
                    f"\n"
                    f"You cannot access a WebSocket server directly "
                    f"with a browser. You need a WebSocket client.\n"
                )
            raise SanicException(msg, status_code=426)
        except InvalidHandshake as exc:
            raise InvalidUsage(f"Failed to open a WebSocket connection: {exc}.\n")
        except Exception as exc:
            msg = (
                    "Failed to open a WebSocket connection.\n"
                    "See server log for more information.\n"
                )
            raise SanicException(msg, status_code=500)

        headers["Sec-WebSocket-Accept"] = accept_key(key)

        if extensions_header is not None:
            headers["Sec-WebSocket-Extensions"] = extensions_header

        if protocol_header is not None:
            headers["Sec-WebSocket-Protocol"] = protocol_header
        headers["Date"] = formatdate(usegmt=True)
        # write the 101 response back to the client
        rv = b"HTTP/1.1 101 Switching Protocols\r\n"
        for k, v in headers.items():
            rv += k.encode("utf-8") + b": " + v.encode("utf-8") + b"\r\n"
        rv += b"\r\n"
        await super().send(rv)
        self.websocket = WebsocketImplProtocol(ws_server, ping_interval=self.websocket_ping_interval, ping_timeout=self.websocket_ping_timeout)
        loop = request.transport.loop if hasattr(request, "transport") and hasattr(request.transport, "loop") else None
        await self.websocket.connection_made(self, loop=loop)
        return self.websocket
 

class WebSocketConnection:
    """
    This is for ASGI Connections.
    It provides an interface similar to WebsocketProtocol, but
    sends/receives over an ASGI connection.
    """
    # TODO
    # - Implement ping/pong

    def __init__(
        self,
        send: Callable[[ASIMessage], Awaitable[None]],
        receive: Callable[[], Awaitable[ASIMessage]],
        subprotocols: Optional[List[str]] = None,
    ) -> None:
        self._send = send
        self._receive = receive
        self.subprotocols = subprotocols or []

    async def send(self, data: Union[str, bytes], *args, **kwargs) -> None:
        message: Dict[str, Union[str, bytes]] = {"type": "websocket.send"}

        if isinstance(data, bytes):
            message.update({"bytes": data})
        else:
            message.update({"text": str(data)})

        await self._send(message)

    async def recv(self, *args, **kwargs) -> Optional[str]:
        message = await self._receive()

        if message["type"] == "websocket.receive":
            return message["text"]
        elif message["type"] == "websocket.disconnect":
            pass

        return None

    receive = recv

    async def accept(self) -> None:
        await self._send(
            {
                "type": "websocket.accept",
                "subprotocol": ",".join(list(self.subprotocols)),
            }
        )

    async def close(self, code: int = 1000, reason: str = "") -> None:
        pass
