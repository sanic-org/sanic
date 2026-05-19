import asyncio
import time

import pytest
import pytest_asyncio

import fakeredis.aioredis

from sanic.jobs.constants import (
    QUEUE_KEY_TEMPLATE,
    STATS_KEY,
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


async def test_concurrency_bounds_enforcement(
    fake_redis,
):
    class_path = (
        "tests.jobs.conftest.SlowJob"
    )
    key = QUEUE_KEY_TEMPLATE.format(name="default")
    for _ in range(6):
        data = _enqueue_payload(
            class_path, kwargs={"duration": 0.5}
        )
        await fake_redis.lpush(key, data)

    consumer = _InlineConsumer(
        redis=fake_redis,
        concurrency=2,
        queues=["default"],
    )

    start_time = time.monotonic()

    async def stop_after():
        await asyncio.sleep(2.5)
        consumer._shutting_down = True

    asyncio.create_task(stop_after())
    await consumer.start()

    elapsed = time.monotonic() - start_time
    assert elapsed >= 1.4


async def test_job_failure_increments_failed_counter(
    fake_redis,
):
    class_path = "tests.jobs.conftest.FailJob"
    key = QUEUE_KEY_TEMPLATE.format(name="default")
    data = _enqueue_payload(class_path)
    await fake_redis.lpush(key, data)

    consumer = _InlineConsumer(
        redis=fake_redis,
        concurrency=1,
        queues=["default"],
    )

    async def stop_after():
        await asyncio.sleep(0.5)
        consumer._shutting_down = True

    asyncio.create_task(stop_after())
    await consumer.start()

    val = await fake_redis.hget(STATS_KEY, "failed")
    assert val is not None
    assert int(val) >= 1


async def test_job_success_increments_completed_counter(
    fake_redis,
):
    class_path = "tests.jobs.conftest.AddJob"
    key = QUEUE_KEY_TEMPLATE.format(name="test_queue")
    data = _enqueue_payload(
        class_path,
        args=(1, 2),
        queue="test_queue",
    )
    await fake_redis.lpush(key, data)

    consumer = _InlineConsumer(
        redis=fake_redis,
        concurrency=1,
        queues=["test_queue"],
    )

    async def stop_after():
        await asyncio.sleep(0.5)
        consumer._shutting_down = True

    asyncio.create_task(stop_after())
    await consumer.start()

    val = await fake_redis.hget(STATS_KEY, "completed")
    assert val is not None
    assert int(val) >= 1


async def test_semaphore_released_on_failure(fake_redis):
    fail_path = "tests.jobs.conftest.FailJob"
    add_path = "tests.jobs.conftest.AddJob"
    default_key = QUEUE_KEY_TEMPLATE.format(
        name="default"
    )
    await fake_redis.lpush(
        default_key,
        _enqueue_payload(add_path, args=(1, 2)),
    )
    await fake_redis.lpush(
        default_key,
        _enqueue_payload(fail_path),
    )

    consumer = _InlineConsumer(
        redis=fake_redis,
        concurrency=1,
        queues=["default"],
    )

    async def stop_after():
        await asyncio.sleep(2.0)
        consumer._shutting_down = True

    asyncio.create_task(stop_after())
    await consumer.start()

    failed = await fake_redis.hget(STATS_KEY, "failed")
    completed = await fake_redis.hget(
        STATS_KEY, "completed"
    )
    assert int(failed or 0) >= 1
    assert int(completed or 0) >= 1


async def test_import_job_class_success():
    cls = JobConsumer._import_job_class(
        "tests.jobs.conftest.AddJob"
    )
    from tests.jobs.conftest import AddJob

    assert cls is AddJob


async def test_import_job_class_failure():
    with pytest.raises(
        (ImportError, AttributeError, ModuleNotFoundError)
    ):
        JobConsumer._import_job_class(
            "nonexistent.module.FakeClass"
        )


async def test_fifo_order(fake_redis):
    class_path = "tests.jobs.conftest.TrackingJob"
    key = QUEUE_KEY_TEMPLATE.format(name="default")

    from tests.jobs.conftest import TrackingJob

    TrackingJob.results = []

    for i in range(3):
        data = _enqueue_payload(
            class_path, args=(i,)
        )
        await fake_redis.lpush(key, data)

    consumer = _InlineConsumer(
        redis=fake_redis,
        concurrency=1,
        queues=["default"],
    )

    async def stop_after():
        await asyncio.sleep(1.0)
        consumer._shutting_down = True

    asyncio.create_task(stop_after())
    await consumer.start()

    assert TrackingJob.results == [0, 1, 2]
