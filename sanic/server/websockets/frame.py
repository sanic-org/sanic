import asyncio
import codecs
from typing import TYPE_CHECKING, Optional, List, AsyncIterator

from websockets.frames import Opcode, Frame
from websockets.typing import Data


UTF8Decoder = codecs.getincrementaldecoder("utf-8")

class WebsocketFrameAssembler:
    """
    Assemble a message from frames.
    Code borrowed from aaugustin/websockets project:
    https://github.com/aaugustin/websockets/blob/6eb98dd8fa5b2c896b9f6be7e8d117708da82a39/src/websockets/sync/messages.py
    """
    __slots__ = ("protocol", "read_mutex", "write_mutex", "message_complete", "message_fetched", "get_in_progress", "decoder", "completed_queue", "chunks", "chunks_queue", "paused", "get_id", "put_id")
    if TYPE_CHECKING:
        protocol: "WebsocketImplProtocol"
        read_mutex: asyncio.Lock
        write_mutex: asyncio.Lock
        message_complete: asyncio.Event
        message_fetched: asyncio.Event
        completed_queue: asyncio.Queue
        get_in_progress: bool
        decoder: Optional[codecs.IncrementalDecoder]
        # For streaming chunks rather than messages:
        chunks: List[Data]
        chunks_queue: Optional[asyncio.Queue[Optional[Data]]]
        paused: bool


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
        self.decoder = None

        # Buffer data from frames belonging to the same message.
        self.chunks = []

        # When switching from "buffering" to "streaming", we use a thread-safe
        # queue for transferring frames from the writing thread (library code)
        # to the reading thread (user code). We're buffering when chunks_queue
        # is None and streaming when it's a Queue. None is a sentinel
        # value marking the end of the stream, superseding message_complete.

        # Stream data from frames belonging to the same message.
        self.chunks_queue = None

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
        #id = self.put_id
        #self.put_id += 1
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
