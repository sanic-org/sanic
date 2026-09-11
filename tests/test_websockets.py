import asyncio
import gc
import re

from asyncio import Event, Queue, TimeoutError
from unittest.mock import Mock, call

import pytest

from websockets.frames import CTRL_OPCODES, DATA_OPCODES, OP_TEXT, Frame

from sanic.exceptions import ServerError
from sanic.server.websockets.frame import WebsocketFrameAssembler
from sanic.server.websockets.impl import OPEN, WebsocketImplProtocol


try:
    from unittest.mock import AsyncMock
except ImportError:
    from tests.asyncmock import AsyncMock  # type: ignore


@pytest.mark.asyncio
async def test_ws_frame_get_message_incomplete_timeout_0():
    assembler = WebsocketFrameAssembler(Mock())
    assembler.message_complete = AsyncMock(spec=Event)
    assembler.message_complete.is_set = Mock(return_value=False)
    data = await assembler.get(0)

    assert data is None
    assembler.message_complete.is_set.assert_called_once()


@pytest.mark.asyncio
async def test_ws_frame_get_message_in_progress():
    assembler = WebsocketFrameAssembler(Mock())
    assembler.get_in_progress = True

    message = re.escape(
        "Called get() on Websocket frame assembler "
        "while asynchronous get is already in progress."
    )

    with pytest.raises(ServerError, match=message):
        await assembler.get()


@pytest.mark.asyncio
async def test_ws_frame_get_message_incomplete():
    assembler = WebsocketFrameAssembler(Mock())
    assembler.message_complete.wait = AsyncMock(return_value=True)
    assembler.message_complete.is_set = Mock(return_value=False)
    data = await assembler.get()

    assert data is None
    assembler.message_complete.wait.assert_awaited_once()


@pytest.mark.asyncio
async def test_ws_frame_get_message():
    assembler = WebsocketFrameAssembler(Mock())
    assembler.message_complete.wait = AsyncMock(return_value=True)
    assembler.message_complete.is_set = Mock(return_value=True)
    data = await assembler.get()

    assert data == b""
    assembler.message_complete.wait.assert_awaited_once()


@pytest.mark.asyncio
async def test_ws_frame_get_message_with_timeout():
    assembler = WebsocketFrameAssembler(Mock())
    assembler.message_complete.wait = AsyncMock(return_value=True)
    assembler.message_complete.is_set = Mock(return_value=True)
    data = await assembler.get(0.1)

    assert data == b""
    assembler.message_complete.wait.assert_awaited_once()
    assert assembler.message_complete.is_set.call_count == 2


@pytest.mark.asyncio
async def test_ws_frame_get_message_with_timeouterror():
    assembler = WebsocketFrameAssembler(Mock())
    assembler.message_complete.wait = AsyncMock(return_value=True)
    assembler.message_complete.is_set = Mock(return_value=True)
    assembler.message_complete.wait.side_effect = TimeoutError("...")
    data = await assembler.get(0.1)

    assert data == b""
    assembler.message_complete.wait.assert_awaited_once()
    assert assembler.message_complete.is_set.call_count == 2


@pytest.mark.asyncio
async def test_ws_frame_get_not_completed():
    assembler = WebsocketFrameAssembler(Mock())
    assembler.message_complete = AsyncMock(spec=Event)
    assembler.message_complete.is_set = Mock(return_value=False)
    data = await assembler.get()

    assert data is None


@pytest.mark.asyncio
async def test_ws_frame_get_not_completed_start():
    assembler = WebsocketFrameAssembler(Mock())
    assembler.message_complete = AsyncMock(spec=Event)
    assembler.message_complete.is_set = Mock(side_effect=[False, True])
    data = await assembler.get(0.1)

    assert data is None


@pytest.mark.asyncio
async def test_ws_frame_get_paused():
    assembler = WebsocketFrameAssembler(Mock())
    assembler.message_complete = AsyncMock(spec=Event)
    assembler.message_complete.is_set = Mock(side_effect=[False, True])
    assembler.paused = True
    data = await assembler.get()

    assert data is None
    assembler.protocol.resume_frames.assert_called_once()


@pytest.mark.asyncio
async def test_ws_frame_get_data():
    assembler = WebsocketFrameAssembler(Mock())
    assembler.message_complete = AsyncMock(spec=Event)
    assembler.message_complete.is_set = Mock(return_value=True)
    assembler.chunks = [b"foo", b"bar"]
    data = await assembler.get()

    assert data == b"foobar"


@pytest.mark.asyncio
async def test_ws_frame_get_iter_in_progress():
    assembler = WebsocketFrameAssembler(Mock())
    assembler.get_in_progress = True

    message = re.escape(
        "Called get_iter on Websocket frame assembler "
        "while asynchronous get is already in progress."
    )

    with pytest.raises(ServerError, match=message):
        [x async for x in assembler.get_iter()]


@pytest.mark.asyncio
async def test_ws_frame_get_iter_none_in_queue():
    assembler = WebsocketFrameAssembler(Mock())
    assembler.message_complete.set()
    assembler.chunks = [b"foo", b"bar"]

    chunks = [x async for x in assembler.get_iter()]

    assert chunks == [b"foo", b"bar"]


@pytest.mark.asyncio
async def test_ws_frame_get_iter_paused():
    assembler = WebsocketFrameAssembler(Mock())
    assembler.message_complete.set()
    assembler.paused = True

    [x async for x in assembler.get_iter()]
    assembler.protocol.resume_frames.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("opcode", DATA_OPCODES)
async def test_ws_frame_put_not_fetched(opcode):
    assembler = WebsocketFrameAssembler(Mock())
    assembler.message_fetched.set()

    message = re.escape(
        "Websocket put() got a new message when the previous message was "
        "not yet fetched."
    )
    with pytest.raises(ServerError, match=message):
        await assembler.put(Frame(opcode, b""))


@pytest.mark.asyncio
@pytest.mark.parametrize("opcode", DATA_OPCODES)
async def test_ws_frame_put_fetched(opcode):
    assembler = WebsocketFrameAssembler(Mock())
    assembler.message_fetched = AsyncMock()
    assembler.message_fetched.is_set = Mock(return_value=False)

    await assembler.put(Frame(opcode, b""))
    assembler.message_fetched.wait.assert_awaited_once()
    assembler.message_fetched.clear.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("opcode", DATA_OPCODES)
async def test_ws_frame_put_message_complete(opcode):
    assembler = WebsocketFrameAssembler(Mock())
    assembler.message_complete.set()

    message = re.escape(
        "Websocket put() got a new message when a message was "
        "already in its chamber."
    )
    with pytest.raises(ServerError, match=message):
        await assembler.put(Frame(opcode, b""))


@pytest.mark.asyncio
@pytest.mark.parametrize("opcode", DATA_OPCODES)
async def test_ws_frame_put_message_into_queue(opcode):
    foo = "foo" if (opcode == OP_TEXT) else b"foo"
    assembler = WebsocketFrameAssembler(Mock())
    assembler.chunks_queue = AsyncMock(spec=Queue)
    assembler.message_fetched = AsyncMock()
    assembler.message_fetched.is_set = Mock(return_value=False)
    await assembler.put(Frame(opcode, b"foo"))

    assert assembler.chunks_queue.put.call_args_list == [call(foo), call(None)]


@pytest.mark.asyncio
@pytest.mark.parametrize("opcode", DATA_OPCODES)
async def test_ws_frame_put_not_fin(opcode):
    assembler = WebsocketFrameAssembler(Mock())

    retval = await assembler.put(Frame(opcode, b"foo", fin=False))

    assert retval is None


@pytest.mark.asyncio
@pytest.mark.parametrize("opcode", CTRL_OPCODES)
async def test_ws_frame_put_skip_ctrl(opcode):
    assembler = WebsocketFrameAssembler(Mock())

    retval = await assembler.put(Frame(opcode, b""))

    assert retval is None


@pytest.mark.asyncio
async def test_connection_lost_cancels_pending_io_tasks():
    """data_received() schedules a fire-and-forget task for
    async_data_received(). On an abrupt disconnect where io_proto.send()
    never resolves, that task must not be left dangling: connection_lost()
    should cancel it via the protocol's own strong reference, instead of
    letting it get garbage-collected while still pending and logging
    "Task was destroyed but it is pending!". Regression for #3175.

    This drives the real data_received() -> async_data_received() ->
    send_data() path (rather than calling the _schedule_io() helper
    directly), and asserts on the actual observable symptom -- the
    loop's exception handler receiving that message -- so the test fails
    for the reported reason on unpatched code, not merely because an
    internal helper doesn't exist yet.
    """
    ws_proto = Mock()
    ws_proto.state = OPEN
    ws_proto.data_to_send = Mock(return_value=[b"pong"])
    ws_proto.events_received = Mock(return_value=[])

    protocol = WebsocketImplProtocol(ws_proto)
    protocol.loop = asyncio.get_running_loop()
    protocol.io_proto = Mock()

    started = asyncio.Event()

    async def send_that_hangs(data):
        started.set()
        # A bare, never-resolved Future -- unlike asyncio.sleep(), which
        # the loop keeps an internal timer-callback reference to -- so
        # nothing keeps the task alive once data_received()'s own local
        # reference goes out of scope.
        await asyncio.Future()

    protocol.io_proto.send = send_that_hangs

    warnings_seen = []
    loop = asyncio.get_running_loop()
    orig_handler = loop.get_exception_handler()
    loop.set_exception_handler(
        lambda loop, context: warnings_seen.append(context.get("message", ""))
    )

    try:
        protocol.data_received(b"irrelevant")
        await started.wait()

        protocol.connection_lost(None)

        # Give the cancellation a few loop turns to actually be
        # delivered and the task to finish, then force a GC pass so
        # anything left unreferenced (as it would be on unpatched code)
        # gets collected and reported here rather than at some later,
        # unrelated point in the suite.
        for _ in range(5):
            await asyncio.sleep(0)
        gc.collect()
        await asyncio.sleep(0)
    finally:
        loop.set_exception_handler(orig_handler)

    assert not any("was destroyed" in w for w in warnings_seen), warnings_seen
    assert protocol.io_tasks == set()
