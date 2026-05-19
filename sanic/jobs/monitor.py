from __future__ import annotations

import argparse
import asyncio
import json
import logging

from typing import Any

from sanic.jobs.constants import (
    ACTIVE_WORKERS_SET,
    KEY_PREFIX,
    STATS_KEY,
    WORKER_KEY_TEMPLATE,
)


logger = logging.getLogger("sanic.jobs")


async def fetch_status(redis_url: str) -> dict[str, Any]:
    """Query Redis and compile telemetry data.

    Args:
        redis_url: Redis connection URL.

    Returns:
        Dict with ``workers``, ``queues``, and ``stats``.
    """
    from redis.asyncio import from_url

    redis = from_url(redis_url)
    try:
        return await _gather_status(redis)
    finally:
        await redis.aclose()


async def fetch_status_from_client(
    redis: Any,
) -> dict[str, Any]:
    """Query Redis using an existing client.

    Args:
        redis: ``redis.asyncio.Redis`` instance.

    Returns:
        Dict with ``workers``, ``queues``, and ``stats``.
    """
    return await _gather_status(redis)


async def _gather_status(
    redis: Any,
) -> dict[str, Any]:
    """Internal: gather all telemetry from Redis."""
    workers: dict[str, Any] = {}
    member_ids = await redis.smembers(ACTIVE_WORKERS_SET)
    stale_ids: list[bytes | str] = []

    for wid_raw in member_ids:
        wid = (
            wid_raw.decode("utf-8") if isinstance(wid_raw, bytes) else wid_raw
        )
        key = WORKER_KEY_TEMPLATE.format(worker_id=wid)
        data = await redis.hgetall(key)
        if not data:
            stale_ids.append(wid_raw)
            continue
        decoded: dict[str, str] = {}
        for k, v in data.items():
            dk = k.decode("utf-8") if isinstance(k, bytes) else k
            dv = v.decode("utf-8") if isinstance(v, bytes) else v
            decoded[dk] = dv
        workers[wid] = {
            "status": decoded.get("state", "unknown"),
            "concurrency_limit": int(decoded.get("concurrency", "0")),
            "active_threads": int(decoded.get("active_jobs", "0")),
            "pid": decoded.get("pid", ""),
            "queues": decoded.get("queues", ""),
            "started_at": decoded.get("started_at", ""),
            "last_heartbeat": decoded.get("last_heartbeat", ""),
        }

    if stale_ids:
        await redis.srem(ACTIVE_WORKERS_SET, *stale_ids)

    queues: dict[str, Any] = {}
    queue_prefix = f"{KEY_PREFIX}:queues:"
    cursor: int | bytes = 0
    while True:
        cursor, keys = await redis.scan(
            cursor=cursor,
            match=f"{queue_prefix}*",
            count=100,
        )
        for key in keys:
            qname_raw = key.decode("utf-8") if isinstance(key, bytes) else key
            qname = qname_raw[len(queue_prefix) :]
            depth = await redis.llen(key)
            queues[qname] = {"enqueued_jobs": depth}
        if cursor == 0 or cursor == b"0":
            break

    raw_stats = await redis.hgetall(STATS_KEY)
    stats: dict[str, int] = {
        "processed_total": 0,
        "failed_total": 0,
        "enqueued_total": 0,
    }
    if raw_stats:
        for k, v in raw_stats.items():
            dk = k.decode("utf-8") if isinstance(k, bytes) else k
            dv = v.decode("utf-8") if isinstance(v, bytes) else str(v)
            if dk == "completed":
                stats["processed_total"] = int(dv)
            elif dk == "failed":
                stats["failed_total"] = int(dv)
            elif dk == "enqueued":
                stats["enqueued_total"] = int(dv)

    return {
        "workers": workers,
        "queues": queues,
        "stats": stats,
    }


def main() -> None:
    """CLI entry point for the job monitor."""
    parser = argparse.ArgumentParser(
        description="Sanic Job Monitor",
    )
    parser.add_argument(
        "--redis-url",
        default="redis://localhost:6379/0",
        help="Redis connection URL",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Output JSON telemetry",
    )
    args = parser.parse_args()
    if args.status:
        result = asyncio.run(fetch_status(args.redis_url))
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
