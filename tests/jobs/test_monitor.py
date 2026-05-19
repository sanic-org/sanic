import pytest
import pytest_asyncio

from sanic.jobs.constants import (
    ACTIVE_WORKERS_SET,
    QUEUE_KEY_TEMPLATE,
    STATS_KEY,
    WORKER_KEY_TEMPLATE,
)
from sanic.jobs.monitor import fetch_status_from_client


pytestmark = pytest.mark.asyncio


async def _setup_worker(redis, worker_id, data):
    key = WORKER_KEY_TEMPLATE.format(
        worker_id=worker_id
    )
    await redis.hset(key, mapping=data)
    await redis.expire(key, 120)
    await redis.sadd(ACTIVE_WORKERS_SET, worker_id)


async def test_fetch_status_json_schema(fake_redis):
    await _setup_worker(
        fake_redis,
        "worker-alpha",
        {
            "pid": "1234",
            "queues": "default,heavy",
            "concurrency": "10",
            "active_jobs": "3",
            "state": "running",
            "started_at": "2026-01-01T00:00:00",
            "last_heartbeat": "2026-01-01T00:01:00",
            "worker_id": "worker-alpha",
        },
    )

    queue_key = QUEUE_KEY_TEMPLATE.format(
        name="default"
    )
    for _ in range(42):
        await fake_redis.lpush(queue_key, b"job")

    heavy_key = QUEUE_KEY_TEMPLATE.format(name="heavy")
    await fake_redis.delete(heavy_key)

    await fake_redis.hset(STATS_KEY, "completed", "1540")
    await fake_redis.hset(STATS_KEY, "failed", "12")
    await fake_redis.hset(STATS_KEY, "enqueued", "1600")

    result = await fetch_status_from_client(fake_redis)

    assert "workers" in result
    assert "queues" in result
    assert "stats" in result

    w = result["workers"]["worker-alpha"]
    assert w["status"] == "running"
    assert w["concurrency_limit"] == 10
    assert w["active_threads"] == 3
    assert w["pid"] == "1234"

    assert result["queues"]["default"]["enqueued_jobs"] == 42

    assert result["stats"]["processed_total"] == 1540
    assert result["stats"]["failed_total"] == 12
    assert result["stats"]["enqueued_total"] == 1600


async def test_fetch_status_empty_state(fake_redis):
    result = await fetch_status_from_client(fake_redis)

    assert result["workers"] == {}
    assert result["queues"] == {}
    assert result["stats"]["processed_total"] == 0
    assert result["stats"]["failed_total"] == 0
    assert result["stats"]["enqueued_total"] == 0


async def test_fetch_status_prunes_expired_workers(
    fake_redis,
):
    await fake_redis.sadd(
        ACTIVE_WORKERS_SET, "stale-worker"
    )

    result = await fetch_status_from_client(fake_redis)

    assert "stale-worker" not in result["workers"]
    is_member = await fake_redis.sismember(
        ACTIVE_WORKERS_SET, "stale-worker"
    )
    assert not is_member


async def test_fetch_status_multiple_workers(fake_redis):
    for i in range(3):
        wid = f"worker-{i}"
        await _setup_worker(
            fake_redis,
            wid,
            {
                "pid": str(1000 + i),
                "queues": "default",
                "concurrency": "5",
                "active_jobs": str(i),
                "state": "running",
                "started_at": "2026-01-01T00:00:00",
                "last_heartbeat": "2026-01-01T00:01:00",
                "worker_id": wid,
            },
        )

    result = await fetch_status_from_client(fake_redis)
    assert len(result["workers"]) == 3
    for i in range(3):
        w = result["workers"][f"worker-{i}"]
        assert w["active_threads"] == i


async def test_fetch_status_multiple_queues(fake_redis):
    for name, count in [
        ("alpha", 10),
        ("beta", 20),
        ("gamma", 0),
    ]:
        key = QUEUE_KEY_TEMPLATE.format(name=name)
        for _ in range(count):
            await fake_redis.lpush(key, b"job")

    result = await fetch_status_from_client(fake_redis)
    assert result["queues"]["alpha"]["enqueued_jobs"] == 10
    assert result["queues"]["beta"]["enqueued_jobs"] == 20
