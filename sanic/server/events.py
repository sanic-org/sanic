from inspect import isawaitable
from typing import Any, Callable, Iterable, Optional


def trigger_events(events: Optional[Iterable[Callable[..., Any]]], loop):
    """
    Trigger event callbacks (functions or async)

    :param events: one or more sync or async functions to execute
    :param loop: event loop
    """
    if events:
        for event in events:
            result = event(loop)
            if isawaitable(result):
                loop.run_until_complete(result)
