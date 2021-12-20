from enum import Enum
from typing import Any, Callable, Dict, Optional, Set, Union

from sanic.models.futures import FutureSignal
from sanic.models.handler_types import SignalHandler
from sanic.signals import Signal


class HashableDict(dict):
    def __hash__(self):
        return hash(tuple(sorted(self.items())))


class SignalMixin:
    def __init__(self, *args, **kwargs) -> None:
        self._future_signals: Set[FutureSignal] = set()

    def _apply_signal(self, signal: FutureSignal) -> Signal:
        raise NotImplementedError  # noqa

    def signal(
        self,
        event: Union[str, Enum],
        *,
        apply: bool = True,
        condition: Dict[str, Any] = None,
    ) -> Callable[[SignalHandler], SignalHandler]:
        """
        For creating a signal handler, used similar to a route handler:

        .. code-block:: python

            @app.signal("foo.bar.<thing>")
            async def signal_handler(thing, **kwargs):
                print(f"[signal_handler] {thing=}", kwargs)

        :param event: Representation of the event in ``one.two.three`` form
        :type event: str
        :param apply: For lazy evaluation, defaults to True
        :type apply: bool, optional
        :param condition: For use with the ``condition`` argument in dispatch
            filtering, defaults to None
        :type condition: Dict[str, Any], optional
        """
        event_value = str(event.value) if isinstance(event, Enum) else event

        def decorator(handler: SignalHandler):
            future_signal = FutureSignal(
                handler, event_value, HashableDict(condition or {})
            )
            self._future_signals.add(future_signal)

            if apply:
                self._apply_signal(future_signal)

            return handler

        return decorator

    def add_signal(
        self,
        handler: Optional[Callable[..., Any]],
        event: str,
        condition: Dict[str, Any] = None,
    ):
        if not handler:

            async def noop():
                ...

            handler = noop
        self.signal(event=event, condition=condition)(handler)
        return handler

    def event(self, event: str):
        raise NotImplementedError
