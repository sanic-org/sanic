import asyncio
import re

from asyncio import Event, Queue, TimeoutError
from itertools import chain
from unittest.mock import Mock, call

import pytest

from websockets.frames import (
    CTRL_OPCODES,
    DATA_OPCODES,
    OP_TEXT,
    Frame,
    Opcode,
)

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


def _make_ws():
    ws_proto = Mock()
    ws_proto.state = OPEN
    return WebsocketImplProtocol(
        ws_proto, ping_interval=None, ping_timeout=None
    )


RECV_CANCEL_CASES = (
    pytest.param(lambda task, ws: task.cancel(), id="task-cancel"),
    pytest.param(lambda task, ws: ws.recv_cancel.cancel(), id="recv-cancel"),
)

RECEIVE_METHODS = (
    pytest.param(lambda ws: ws.recv(timeout=5), id="recv"),
    pytest.param(lambda ws: ws.recv_burst(), id="recv-burst"),
)


@pytest.mark.asyncio
@pytest.mark.parametrize("cancel_fn", RECV_CANCEL_CASES)
@pytest.mark.parametrize("receive", RECEIVE_METHODS)
async def test_ws_recv_cancel_awaits_assembler_task(receive, cancel_fn):
    ws = _make_ws()

    get_started = asyncio.Event()
    get_finished = asyncio.Event()

    async def slow_get(timeout=None):
        get_started.set()
        try:
            await asyncio.sleep(10)
        finally:
            get_finished.set()

    ws.assembler = Mock()
    ws.assembler.get = slow_get

    recv_task = asyncio.create_task(receive(ws))
    await get_started.wait()

    finished_before_return = False
    original_release = ws.recv_lock.release

    def check_on_release():
        nonlocal finished_before_return
        finished_before_return = get_finished.is_set()
        original_release()

    ws.recv_lock.release = check_on_release

    cancel_fn(recv_task, ws)

    with pytest.raises(asyncio.CancelledError):
        await recv_task

    assert finished_before_return, (
        "assembler.get() coroutine was still pending when recv() "
        "returned — would cause 'Task was destroyed but it is "
        "pending' on shutdown"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("cancel_fn", RECV_CANCEL_CASES)
@pytest.mark.parametrize(
    ("frames_before_cancel", "frames_after_cancel"),
    (
        pytest.param(
            (),
            (Frame(OP_TEXT, b"hello"),),
            id="before-first-frame",
        ),
        pytest.param(
            (Frame(OP_TEXT, b"he", fin=False),),
            (
                Frame(Opcode.CONT, b"ll", fin=False),
                Frame(Opcode.CONT, b"o"),
            ),
            id="after-first-fragment",
        ),
    ),
)
async def test_ws_recv_cancel_keeps_assembler_usable(
    cancel_fn, frames_before_cancel, frames_after_cancel
):
    ws = _make_ws()

    recv_task = asyncio.create_task(ws.recv(timeout=5))
    for _ in range(10):
        if ws.recv_cancel is not None and ws.assembler.get_in_progress:
            break
        await asyncio.sleep(0)

    assert ws.recv_cancel is not None
    assert ws.assembler.get_in_progress is True

    for frame in frames_before_cancel:
        await ws.assembler.put(frame)

    cancel_fn(recv_task, ws)

    with pytest.raises(asyncio.CancelledError):
        await recv_task

    async def deliver_rest():
        for frame in frames_after_cancel:
            await ws.assembler.put(frame)

    put_task = asyncio.create_task(deliver_rest())

    expected = b"".join(
        frame.data
        for frame in chain(frames_before_cancel, frames_after_cancel)
    ).decode()
    assert await ws.recv(timeout=1) == expected
    await put_task
