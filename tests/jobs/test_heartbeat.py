import asyncio

import pytest
import pytest_asyncio

from sanic.jobs.constants import (
    ACTIVE_WORKERS_SET,
    WORKER_KEY_TEMPLATE,
)
from sanic.jobs.heartbeat import run_heartbeat


pytestmark = pytest.mark.asyncio


def _make_status():
    return {
        "pid": "12345",
        "queues": "default",
        "concurrency": "5",
        "active_jobs": "2",
        "state": "running",
        "started_at": "2026-01-01T00:00:00",
    }


async def test_heartbeat_writes_worker_key(fake_redis):
    worker_id = "test-heartbeat-1"
    task = asyncio.create_task(
        run_heartbeat(
            redis=fake_redis,
            worker_id=worker_id,
            interval=60,
            ttl=120,
            get_status=_make_status,
        )
    )
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    key = WORKER_KEY_TEMPLATE.format(
        worker_id=worker_id
    )
    data = await fake_redis.hgetall(key)
    assert data
    decoded = {
        (
            k.decode("utf-8")
            if isinstance(k, bytes)
            else k
        ): (
            v.decode("utf-8")
            if isinstance(v, bytes)
            else v
        )
        for k, v in data.items()
    }
    assert decoded["pid"] == "12345"
    assert decoded["state"] == "running"
    assert decoded["worker_id"] == worker_id
    assert "last_heartbeat" in decoded


async def test_heartbeat_sets_ttl(fake_redis):
    worker_id = "test-heartbeat-ttl"
    task = asyncio.create_task(
        run_heartbeat(
            redis=fake_redis,
            worker_id=worker_id,
            interval=60,
            ttl=120,
            get_status=_make_status,
        )
    )
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    key = WORKER_KEY_TEMPLATE.format(
        worker_id=worker_id
    )
    ttl = await fake_redis.ttl(key)
    assert ttl > 0
    assert ttl <= 120


async def test_heartbeat_adds_to_active_workers(
    fake_redis,
):
    worker_id = "test-heartbeat-active"
    task = asyncio.create_task(
        run_heartbeat(
            redis=fake_redis,
            worker_id=worker_id,
            interval=60,
            ttl=120,
            get_status=_make_status,
        )
    )
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    is_member = await fake_redis.sismember(
        ACTIVE_WORKERS_SET, worker_id
    )
    assert is_member


async def test_heartbeat_updates_on_interval(fake_redis):
    call_count = {"n": 0}

    def counting_status():
        call_count["n"] += 1
        return _make_status()

    worker_id = "test-heartbeat-interval"
    task = asyncio.create_task(
        run_heartbeat(
            redis=fake_redis,
            worker_id=worker_id,
            interval=0.05,
            ttl=120,
            get_status=counting_status,
        )
    )
    await asyncio.sleep(0.18)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    assert call_count["n"] >= 2
