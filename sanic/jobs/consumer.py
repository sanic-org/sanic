from __future__ import annotations

import argparse
import asyncio
import logging
import os
import signal
import uuid

from datetime import datetime, timezone
from importlib import import_module
from typing import Any

from sanic.jobs.constants import (
    ACTIVE_WORKERS_SET,
    DEFAULT_BRPOP_TIMEOUT,
    DEFAULT_CONCURRENCY,
    DEFAULT_HEARTBEAT_INTERVAL,
    DEFAULT_HEARTBEAT_TTL,
    DEFAULT_SHUTDOWN_TIMEOUT,
    QUEUE_KEY_TEMPLATE,
    STATS_KEY,
    WORKER_KEY_TEMPLATE,
)
from sanic.jobs.heartbeat import run_heartbeat
from sanic.jobs.serializer import deserialize_job


logger = logging.getLogger("sanic.jobs")


class JobConsumer:
    """Standalone job consumer that pulls and executes
    jobs from Redis queues.

    Args:
        redis_url: Redis connection URL.
        queues: List of queue names to poll.
        concurrency: Maximum concurrent jobs.
        shutdown_timeout: Seconds to wait for active jobs
            during graceful shutdown.
        heartbeat_interval: Seconds between heartbeats.
    """

    __slots__ = (
        "_active_tasks",
        "_concurrency",
        "_heartbeat_interval",
        "_heartbeat_task",
        "_poll_task",
        "_queues",
        "_redis",
        "_redis_url",
        "_semaphore",
        "_shutdown_timeout",
        "_shutting_down",
        "_started_at",
        "_worker_id",
    )

    def __init__(
        self,
        redis_url: str,
        queues: list[str] | None = None,
        concurrency: int = DEFAULT_CONCURRENCY,
        shutdown_timeout: int = DEFAULT_SHUTDOWN_TIMEOUT,
        heartbeat_interval: int = DEFAULT_HEARTBEAT_INTERVAL,
    ) -> None:
        self._redis_url = redis_url
        self._queues = queues or ["default"]
        self._concurrency = concurrency
        self._shutdown_timeout = shutdown_timeout
        self._heartbeat_interval = heartbeat_interval
        self._worker_id = f"worker-{os.getpid()}-{uuid.uuid4().hex[:8]}"
        self._redis: Any = None
        self._semaphore: asyncio.BoundedSemaphore | None = None
        self._active_tasks: set[asyncio.Task[None]] = set()
        self._shutting_down = False
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._poll_task: asyncio.Task[None] | None = None
        self._started_at = ""

    async def start(self) -> None:
        """Connect to Redis and begin processing jobs."""
        from redis.asyncio import from_url

        self._redis = from_url(self._redis_url)
        self._semaphore = asyncio.BoundedSemaphore(self._concurrency)
        self._started_at = datetime.now(tz=timezone.utc).isoformat()
        self._setup_signals()
        self._heartbeat_task = asyncio.create_task(
            run_heartbeat(
                redis=self._redis,
                worker_id=self._worker_id,
                interval=self._heartbeat_interval,
                ttl=DEFAULT_HEARTBEAT_TTL,
                get_status=self._get_status,
            )
        )
        logger.info(
            "Worker %s started (concurrency=%d, queues=%s)",
            self._worker_id,
            self._concurrency,
            ",".join(self._queues),
        )
        await self._poll_loop()

    async def _poll_loop(self) -> None:
        """Main loop: acquire semaphore, BRPOP, dispatch."""
        queue_keys = [QUEUE_KEY_TEMPLATE.format(name=q) for q in self._queues]
        assert self._semaphore is not None
        while not self._shutting_down:
            await self._semaphore.acquire()
            if self._shutting_down:
                self._semaphore.release()
                break
            try:
                result = await self._redis.brpop(
                    *queue_keys,
                    timeout=DEFAULT_BRPOP_TIMEOUT,
                )
            except asyncio.CancelledError:
                self._semaphore.release()
                break
            except Exception:
                logger.exception("BRPOP error")
                self._semaphore.release()
                continue
            if result is None:
                self._semaphore.release()
                continue
            _queue_key, raw_data = result
            task = asyncio.create_task(self._execute_job(raw_data))
            self._active_tasks.add(task)
            task.add_done_callback(self._task_done)

    async def _execute_job(self, raw_data: bytes) -> None:
        """Deserialize, import, instantiate, and run a job."""
        payload: dict[str, Any] = {}
        try:
            payload = deserialize_job(raw_data)
            class_path = payload["class"]
            args = payload.get("args", [])
            kwargs = payload.get("kwargs", {})
            job_cls = self._import_job_class(class_path)
            job = job_cls()
            logger.debug(
                "Executing job %s (%s)",
                payload.get("id", "?"),
                class_path,
            )
            await job.perform(*args, **kwargs)
            await self._redis.hincrby(STATS_KEY, "completed", 1)
            logger.debug(
                "Job %s completed",
                payload.get("id", "?"),
            )
        except Exception:
            await self._redis.hincrby(STATS_KEY, "failed", 1)
            logger.exception(
                "Job %s failed",
                payload.get("id", "?"),
            )

    def _task_done(self, task: asyncio.Task[None]) -> None:
        """Callback: release semaphore, remove from set."""
        self._active_tasks.discard(task)
        if self._semaphore is not None:
            self._semaphore.release()
        exc = task.exception() if not task.cancelled() else None
        if exc:
            logger.error("Task exception: %s", exc, exc_info=exc)

    async def shutdown(self) -> None:
        """Gracefully stop accepting jobs and drain."""
        if self._shutting_down:
            logger.warning("Force shutdown requested")
            for t in list(self._active_tasks):
                t.cancel()
            return
        self._shutting_down = True
        logger.info(
            "Shutting down worker %s (%d active jobs, timeout=%ds)",
            self._worker_id,
            len(self._active_tasks),
            self._shutdown_timeout,
        )
        if self._active_tasks:
            done, pending = await asyncio.wait(
                self._active_tasks,
                timeout=self._shutdown_timeout,
            )
            for t in pending:
                t.cancel()
            if pending:
                await asyncio.wait(pending, timeout=1.0)
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        if self._redis is not None:
            try:
                key = WORKER_KEY_TEMPLATE.format(worker_id=self._worker_id)
                pipe = self._redis.pipeline()
                pipe.delete(key)
                pipe.srem(ACTIVE_WORKERS_SET, self._worker_id)
                await pipe.execute()
            except Exception:
                logger.exception("Error cleaning up Redis state")
            await self._redis.aclose()
        logger.info("Worker %s shut down", self._worker_id)

    def _setup_signals(self) -> None:
        """Register SIGINT/SIGTERM handlers."""
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig,
                lambda: asyncio.ensure_future(self.shutdown()),
            )

    def _get_status(self) -> dict[str, str]:
        """Build current status dict for heartbeat."""
        return {
            "pid": str(os.getpid()),
            "queues": ",".join(self._queues),
            "concurrency": str(self._concurrency),
            "active_jobs": str(len(self._active_tasks)),
            "state": ("shutting_down" if self._shutting_down else "running"),
            "started_at": self._started_at,
        }

    @staticmethod
    def _import_job_class(class_path: str) -> type:
        """Dynamically import a job class by path."""
        module_path, class_name = class_path.rsplit(".", 1)
        module = import_module(module_path)
        return getattr(module, class_name)


def main() -> None:
    """CLI entry point for the job consumer."""
    parser = argparse.ArgumentParser(
        description="Sanic Job Worker Consumer",
    )
    parser.add_argument(
        "--redis-url",
        default="redis://localhost:6379/0",
        help="Redis connection URL",
    )
    parser.add_argument(
        "--queues",
        default="default",
        help="Comma-separated queue names",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help="Max concurrent jobs",
    )
    parser.add_argument(
        "--shutdown-timeout",
        type=int,
        default=DEFAULT_SHUTDOWN_TIMEOUT,
        help="Graceful shutdown timeout (seconds)",
    )
    parser.add_argument(
        "--heartbeat-interval",
        type=int,
        default=DEFAULT_HEARTBEAT_INTERVAL,
        help="Heartbeat interval (seconds)",
    )
    args = parser.parse_args()
    queues = [q.strip() for q in args.queues.split(",")]
    logging.basicConfig(
        level=logging.INFO,
        format=("%(asctime)s [%(levelname)s] %(name)s: %(message)s"),
    )
    consumer = JobConsumer(
        redis_url=args.redis_url,
        queues=queues,
        concurrency=args.concurrency,
        shutdown_timeout=args.shutdown_timeout,
        heartbeat_interval=args.heartbeat_interval,
    )
    try:
        asyncio.run(consumer.start())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
