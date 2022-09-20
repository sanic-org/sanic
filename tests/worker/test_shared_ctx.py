# 18
# 21-29
# 26
# 36-37
# 42
# 55
# 38->

import logging

from ctypes import c_int32
from multiprocessing import Pipe, Queue, Value
from os import environ
from typing import Any

import pytest

from sanic.types.shared_ctx import SharedContext


@pytest.mark.parametrize(
    "item,okay",
    (
        (Pipe(), True),
        (Value("i", 0), True),
        (Queue(), True),
        (c_int32(1), True),
        (1, False),
        ("thing", False),
        (object(), False),
    ),
)
def test_set_items(item: Any, okay: bool, caplog):
    ctx = SharedContext()

    with caplog.at_level(logging.INFO):
        ctx.item = item

    assert ctx.is_locked is False
    assert len(caplog.record_tuples) == 0 if okay else 1
    if not okay:
        assert caplog.record_tuples[0][0] == "sanic.error"
        assert caplog.record_tuples[0][1] == logging.WARNING
        assert "Unsafe object" in caplog.record_tuples[0][2]


@pytest.mark.parametrize(
    "item",
    (
        Pipe(),
        Value("i", 0),
        Queue(),
        c_int32(1),
        1,
        "thing",
        object(),
    ),
)
def test_set_items_in_worker(item: Any, caplog):
    ctx = SharedContext()

    environ["SANIC_WORKER_NAME"] = "foo"
    with caplog.at_level(logging.INFO):
        ctx.item = item
    del environ["SANIC_WORKER_NAME"]

    assert ctx.is_locked is False
    assert len(caplog.record_tuples) == 0


def test_lock():
    ctx = SharedContext()

    assert ctx.is_locked is False

    ctx.lock()

    assert ctx.is_locked is True

    message = "Cannot set item on locked SharedContext object"
    with pytest.raises(RuntimeError, match=message):
        ctx.item = 1
