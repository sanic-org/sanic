from __future__ import annotations

from inspect import isawaitable
from typing import TYPE_CHECKING, Any, Callable, Iterable, Optional


if TYPE_CHECKING:
    from sanic import Sanic


def trigger_events(
    events: Optional[Iterable[Callable[..., Any]]],
    loop,
    app: Optional[Sanic] = None,
):
    """
    Trigger event callbacks (functions or async)

    :param events: one or more sync or async functions to execute
    :param loop: event loop
    """
    if events:
        for event in events:
            try:
                result = event() if not app else event(app)
            except TypeError:
                result = event(loop) if not app else event(app, loop)
            if isawaitable(result):
                loop.run_until_complete(result)
