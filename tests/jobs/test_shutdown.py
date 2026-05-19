import asyncio
import time

import pytest
import pytest_asyncio

from sanic.jobs.constants import (
    QUEUE_KEY_TEMPLATE,
    STATS_KEY,
    ACTIVE_WORKERS_SET,
    WORKER_KEY_TEMPLATE,
)
from sanic.jobs.consumer import JobConsumer
from sanic.jobs.serializer import serialize_job


pytestmark = pytest.mark.asyncio


def _enqueue_payload(
    class_path, args=(), kwargs=None, queue="default"
):
    import uuid
    from datetime import datetime, timezone

    return serialize_job(
        job_class_path=class_path,
        args=args,
        kwargs=kwargs or {},
        job_id=str(uuid.uuid4()),
        queue=queue,
        enqueued_at=(
            datetime.now(tz=timezone.utc).isoformat()
        ),
    )


class _InlineConsumer(JobConsumer):
    """Consumer that uses a provided fake redis."""

    __slots__ = ("_provided_redis",)

    def __init__(self, redis, **kwargs):
        super().__init__(
            redis_url="redis://fake", **kwargs
        )
        self._provided_redis = redis

    async def start(self) -> None:
        self._redis = self._provided_redis
        self._semaphore = asyncio.BoundedSemaphore(
            self._concurrency
        )
        from datetime import datetime, timezone

        self._started_at = (
            datetime.now(tz=timezone.utc).isoformat()
        )
        self._heartbeat_task = asyncio.create_task(
            asyncio.sleep(999)
        )
        await self._poll_loop()


async def test_shutdown_waits_for_active_tasks(
    fake_redis,
):
    class_path = "tests.jobs.conftest.SlowJob"
    key = QUEUE_KEY_TEMPLATE.format(name="default")
    data = _enqueue_payload(
        class_path, kwargs={"duration": 0.3}
    )
    await fake_redis.lpush(key, data)

    consumer = _InlineConsumer(
        redis=fake_redis,
        concurrency=1,
        queues=["default"],
        shutdown_timeout=5,
    )

    async def trigger_shutdown():
        await asyncio.sleep(0.1)
        await consumer.shutdown()

    poll_task = asyncio.create_task(consumer.start())
    asyncio.create_task(trigger_shutdown())
    await poll_task

    val = await fake_redis.hget(STATS_KEY, "completed")
    assert val is not None
    assert int(val) >= 1


async def test_shutdown_cancels_after_timeout(
    fake_redis,
):
    class_path = "tests.jobs.conftest.SlowJob"
    key = QUEUE_KEY_TEMPLATE.format(name="default")
    data = _enqueue_payload(
        class_path, kwargs={"duration": 10.0}
    )
    await fake_redis.lpush(key, data)

    consumer = _InlineConsumer(
        redis=fake_redis,
        concurrency=1,
        queues=["default"],
        shutdown_timeout=0,
    )

    start = time.monotonic()

    async def trigger_shutdown():
        await asyncio.sleep(0.2)
        await consumer.shutdown()

    poll_task = asyncio.create_task(consumer.start())
    asyncio.create_task(trigger_shutdown())
    await poll_task

    elapsed = time.monotonic() - start
    assert elapsed < 3.0


async def test_shutdown_stops_accepting_new_jobs(
    fake_redis,
):
    class_path = "tests.jobs.conftest.SlowJob"
    key = QUEUE_KEY_TEMPLATE.format(name="default")
    for _ in range(5):
        data = _enqueue_payload(
            class_path, kwargs={"duration": 0.3}
        )
        await fake_redis.lpush(key, data)

    consumer = _InlineConsumer(
        redis=fake_redis,
        concurrency=1,
        queues=["default"],
        shutdown_timeout=2,
    )

    async def trigger_shutdown():
        await asyncio.sleep(0.2)
        await consumer.shutdown()

    poll_task = asyncio.create_task(consumer.start())
    asyncio.create_task(trigger_shutdown())
    await poll_task

    completed_raw = await fake_redis.hget(
        STATS_KEY, "completed"
    )
    completed = int(completed_raw or 0)
    assert completed < 5


async def test_connection_pool_cleanup(fake_redis):
    consumer = _InlineConsumer(
        redis=fake_redis,
        concurrency=1,
        queues=["default"],
    )

    consumer._redis = fake_redis
    consumer._semaphore = asyncio.BoundedSemaphore(1)
    consumer._heartbeat_task = asyncio.create_task(
        asyncio.sleep(999)
    )
    consumer._started_at = "2026-01-01T00:00:00"

    await consumer.shutdown()
    assert consumer._shutting_down is True
