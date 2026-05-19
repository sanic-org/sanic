import asyncio

import pytest
import pytest_asyncio

import fakeredis.aioredis

from sanic.jobs.base import SanicJob


@pytest_asyncio.fixture
async def fake_redis():
    r = fakeredis.aioredis.FakeRedis()
    yield r
    await r.aclose()


class AddJob(SanicJob):
    __slots__ = ()
    queue = "test_queue"

    async def perform(self, a, b):
        return a + b


class SlowJob(SanicJob):
    __slots__ = ()
    queue = "default"

    async def perform(self, duration=0.5):
        await asyncio.sleep(duration)


class FailJob(SanicJob):
    __slots__ = ()
    queue = "default"

    async def perform(self):
        raise ValueError("deliberate failure")


class TrackingJob(SanicJob):
    __slots__ = ()
    queue = "default"
    results: list = []

    async def perform(self, value):
        TrackingJob.results.append(value)


@pytest.fixture
def add_job_class():
    return AddJob


@pytest.fixture
def slow_job_class():
    return SlowJob


@pytest.fixture
def fail_job_class():
    return FailJob


@pytest.fixture
def tracking_job_class():
    TrackingJob.results = []
    return TrackingJob
