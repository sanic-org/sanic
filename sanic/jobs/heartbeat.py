from __future__ import annotations

import asyncio
import logging

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from sanic.jobs.constants import (
    ACTIVE_WORKERS_SET,
    WORKER_KEY_TEMPLATE,
)


logger = logging.getLogger("sanic.jobs")


async def run_heartbeat(
    redis: Any,
    worker_id: str,
    interval: int,
    ttl: int,
    get_status: Callable[[], dict[str, str]],
) -> None:
    """Write worker heartbeat to Redis periodically.

    The worker hash key is set with a TTL so it
    auto-expires if the worker crashes.

    Args:
        redis: ``redis.asyncio.Redis`` instance.
        worker_id: Unique worker identifier.
        interval: Seconds between heartbeats.
        ttl: TTL for the worker key in seconds.
        get_status: Returns current worker status dict.
    """
    key = WORKER_KEY_TEMPLATE.format(worker_id=worker_id)
    try:
        while True:
            status = get_status()
            status["last_heartbeat"] = datetime.now(
                tz=timezone.utc
            ).isoformat()
            status["worker_id"] = worker_id
            pipe = redis.pipeline()
            pipe.delete(key)
            pipe.hset(key, mapping=status)
            pipe.expire(key, ttl)
            pipe.sadd(ACTIVE_WORKERS_SET, worker_id)
            await pipe.execute()
            logger.debug(
                "Heartbeat sent for worker %s",
                worker_id,
            )
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logger.debug(
            "Heartbeat stopped for worker %s",
            worker_id,
        )
