from __future__ import annotations

import logging
import uuid

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from sanic.jobs.constants import QUEUE_KEY_TEMPLATE, STATS_KEY
from sanic.jobs.serializer import serialize_job


logger = logging.getLogger("sanic.jobs")


class SanicJob(ABC):
    """Base class for background jobs.

    Subclass this and implement ``perform`` to define a job.

    Class attributes:
        queue: Target queue name. Default ``"default"``.
        max_retries: Maximum retry attempts. Default ``3``.
        retry_delay: Delay between retries in seconds.
            Default ``5``.
    """

    __slots__ = ()

    queue: str = "default"
    max_retries: int = 3
    retry_delay: int = 5

    @abstractmethod
    async def perform(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the job. Must be overridden."""
        ...

    @classmethod
    async def perform_later(
        cls,
        redis_client: Any,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """Enqueue a job for background execution.

        Args:
            redis_client: A ``redis.asyncio.Redis`` instance.
            *args: Positional arguments for ``perform()``.
            **kwargs: Keyword arguments for ``perform()``.

        Returns:
            The job ID (UUID4 string).
        """
        job_id = str(uuid.uuid4())
        class_path = f"{cls.__module__}.{cls.__qualname__}"
        enqueued_at = datetime.now(tz=timezone.utc).isoformat()
        data = serialize_job(
            job_class_path=class_path,
            args=args,
            kwargs=kwargs,
            job_id=job_id,
            queue=cls.queue,
            enqueued_at=enqueued_at,
        )
        queue_key = QUEUE_KEY_TEMPLATE.format(name=cls.queue)
        pipe = redis_client.pipeline()
        pipe.lpush(queue_key, data)
        pipe.hincrby(STATS_KEY, "enqueued", 1)
        await pipe.execute()
        logger.debug("Enqueued job %s on queue %s", job_id, cls.queue)
        return job_id
