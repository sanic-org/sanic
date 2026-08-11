import asyncio
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
    """An IO task scheduled from data_received/eof_received (eg via
    _schedule_io) must not be left dangling on an abrupt disconnect: it
    should be referenced on the protocol and cancelled by connection_lost,
    instead of getting garbage-collected while still pending and logging
    "Task was destroyed but it is pending!". Regression for #3175.
    """
    ws_proto = Mock()
    ws_proto.state = OPEN
    protocol = WebsocketImplProtocol(ws_proto)
    protocol.loop = asyncio.get_running_loop()

    started = asyncio.Event()

    async def never_completes():
        started.set()
        await asyncio.sleep(1000)

    task = protocol._schedule_io(never_completes())
    await started.wait()
    assert task in protocol.io_tasks
    assert not task.done()

    protocol.connection_lost(None)

    with pytest.raises(asyncio.CancelledError):
        await task
    assert task.cancelled()
    # The done-callback discards the task from io_tasks once cancellation
    # actually completes; give the loop a turn to run it.
    await asyncio.sleep(0)
    assert task not in protocol.io_tasks
