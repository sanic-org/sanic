from enum import IntEnum, auto


class JobState(IntEnum):
    """Job lifecycle states."""

    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    RETRYING = auto()


KEY_PREFIX = "sanic_jobs"
QUEUE_KEY_TEMPLATE = f"{KEY_PREFIX}:queues:{{name}}"
WORKER_KEY_TEMPLATE = f"{KEY_PREFIX}:workers:{{worker_id}}"
STATS_KEY = f"{KEY_PREFIX}:stats"
ACTIVE_WORKERS_SET = f"{KEY_PREFIX}:active_workers"

DEFAULT_HEARTBEAT_INTERVAL = 5
DEFAULT_HEARTBEAT_TTL = 15
DEFAULT_SHUTDOWN_TIMEOUT = 30
DEFAULT_CONCURRENCY = 10
DEFAULT_BRPOP_TIMEOUT = 1
