import uuid

import pytest
import pytest_asyncio

from sanic.jobs.base import SanicJob
from sanic.jobs.constants import QUEUE_KEY_TEMPLATE, STATS_KEY
from sanic.jobs.serializer import deserialize_job


pytestmark = pytest.mark.asyncio


async def test_perform_later_enqueues_job(
    fake_redis, add_job_class
):
    job_id = await add_job_class.perform_later(
        fake_redis, 1, 2
    )
    key = QUEUE_KEY_TEMPLATE.format(name="test_queue")
    length = await fake_redis.llen(key)
    assert length == 1
    assert uuid.UUID(job_id, version=4)


async def test_perform_later_increments_enqueued_stat(
    fake_redis, add_job_class
):
    await add_job_class.perform_later(fake_redis, 1, 2)
    val = await fake_redis.hget(STATS_KEY, "enqueued")
    assert int(val) == 1

    await add_job_class.perform_later(fake_redis, 3, 4)
    val = await fake_redis.hget(STATS_KEY, "enqueued")
    assert int(val) == 2


async def test_perform_later_serialization_format(
    fake_redis, add_job_class
):
    job_id = await add_job_class.perform_later(
        fake_redis, 10, b=20
    )
    key = QUEUE_KEY_TEMPLATE.format(name="test_queue")
    raw = await fake_redis.rpop(key)
    payload = deserialize_job(raw)

    assert payload["id"] == job_id
    assert payload["class"].endswith("AddJob")
    assert payload["queue"] == "test_queue"
    assert payload["args"] == [10]
    assert payload["kwargs"] == {"b": 20}
    assert "enqueued_at" in payload
    assert payload["retry_count"] == 0


async def test_perform_later_uses_class_queue(
    fake_redis,
):
    class CriticalJob(SanicJob):
        __slots__ = ()
        queue = "critical"

        async def perform(self):
            pass

    await CriticalJob.perform_later(fake_redis)
    key = QUEUE_KEY_TEMPLATE.format(name="critical")
    length = await fake_redis.llen(key)
    assert length == 1


async def test_perform_is_abstract():
    with pytest.raises(TypeError):
        SanicJob()


async def test_multiple_enqueues_fifo_order(
    fake_redis, add_job_class
):
    ids = []
    for i in range(5):
        jid = await add_job_class.perform_later(
            fake_redis, i, 0
        )
        ids.append(jid)

    key = QUEUE_KEY_TEMPLATE.format(name="test_queue")
    for expected_id in ids:
        raw = await fake_redis.rpop(key)
        payload = deserialize_job(raw)
        assert payload["id"] == expected_id
