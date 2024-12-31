from __future__ import annotations

from collections.abc import Iterable
from inspect import isawaitable
from typing import TYPE_CHECKING, Any, Callable, Optional


if TYPE_CHECKING:
    from sanic import Sanic


def trigger_events(
    events: Optional[Iterable[Callable[..., Any]]],
    loop,
    app: Optional[Sanic] = None,
    **kwargs,
):
    """Trigger event callbacks (functions or async)

    Args:
        events (Optional[Iterable[Callable[..., Any]]]): [description]
        loop ([type]): [description]
        app (Optional[Sanic], optional): [description]. Defaults to None.
    """
    if events:
        for event in events:
            try:
                result = event(**kwargs) if not app else event(app, **kwargs)
            except TypeError:
                result = (
                    event(loop, **kwargs)
                    if not app
                    else event(app, loop, **kwargs)
                )
            if isawaitable(result):
                loop.run_until_complete(result)
