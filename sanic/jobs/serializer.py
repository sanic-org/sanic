from __future__ import annotations

from functools import partial
from typing import Any

from sanic.jobs.exceptions import (
    JobDeserializationError,
    JobSerializationError,
)


try:
    from ujson import dumps as json_dumps
    from ujson import loads as json_loads
except ModuleNotFoundError:
    from json import dumps, loads  # type: ignore[assignment]

    json_dumps = partial(dumps, separators=(",", ":"))  # type: ignore
    json_loads = loads  # type: ignore


def serialize_job(
    job_class_path: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    job_id: str,
    queue: str,
    enqueued_at: str,
    retry_count: int = 0,
) -> bytes:
    """Serialize a job payload to JSON bytes.

    Args:
        job_class_path: Fully qualified class path.
        args: Positional arguments for perform().
        kwargs: Keyword arguments for perform().
        job_id: Unique job identifier (UUID4).
        queue: Target queue name.
        enqueued_at: ISO timestamp of enqueue time.
        retry_count: Current retry attempt number.

    Returns:
        UTF-8 encoded JSON bytes.
    """
    payload = {
        "id": job_id,
        "class": job_class_path,
        "queue": queue,
        "args": list(args),
        "kwargs": kwargs,
        "enqueued_at": enqueued_at,
        "retry_count": retry_count,
    }
    try:
        return json_dumps(payload).encode("utf-8")
    except (TypeError, ValueError) as e:
        raise JobSerializationError(f"Failed to serialize job: {e}") from e


def deserialize_job(data: bytes) -> dict[str, Any]:
    """Deserialize a job payload from JSON bytes.

    Args:
        data: UTF-8 encoded JSON bytes.

    Returns:
        Parsed job payload dict.
    """
    try:
        return json_loads(data)
    except (TypeError, ValueError) as e:
        raise JobDeserializationError(f"Failed to deserialize job: {e}") from e
