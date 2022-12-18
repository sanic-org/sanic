from enum import Enum
from typing import Any, Callable, Dict, Optional, Set, Union

from sanic.base.meta import SanicMeta
from sanic.models.futures import FutureSignal
from sanic.models.handler_types import SignalHandler
from sanic.signals import Signal
from sanic.types import HashableDict


class SignalMixin(metaclass=SanicMeta):
    def __init__(self, *args, **kwargs) -> None:
        self._future_signals: Set[FutureSignal] = set()

    def _apply_signal(self, signal: FutureSignal) -> Signal:
        raise NotImplementedError  # noqa

    def signal(
        self,
        event: Union[str, Enum],
        *,
        apply: bool = True,
        condition: Optional[Dict[str, Any]] = None,
        exclusive: bool = True,
    ) -> Callable[[SignalHandler], SignalHandler]:
        """
        For creating a signal handler, used similar to a route handler:

        .. code-block:: python

            @app.signal("foo.bar.<thing>")
            async def signal_handler(thing, **kwargs):
                print(f"[signal_handler] {thing=}", kwargs)

        :param event: Representation of the event in ``one.two.three`` form
        :type event: str
        :param apply: For lazy evaluation, defaults to ``True``
        :type apply: bool, optional
        :param condition: For use with the ``condition`` argument in dispatch
            filtering, defaults to ``None``
        :param exclusive: When ``True``, the signal can only be dispatched
            when the condition has been met. When ``False``, the signal can
            be dispatched either with or without it. *THIS IS INAPPLICABLE TO
            BLUEPRINT SIGNALS. THEY ARE ALWAYS NON-EXCLUSIVE*, defaults
            to ``True``
        :type condition: Dict[str, Any], optional
        """
        event_value = str(event.value) if isinstance(event, Enum) else event

        def decorator(handler: SignalHandler):
            future_signal = FutureSignal(
                handler, event_value, HashableDict(condition or {}), exclusive
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
        condition: Optional[Dict[str, Any]] = None,
        exclusive: bool = True,
    ):
        if not handler:

            async def noop():
                ...

            handler = noop
        self.signal(event=event, condition=condition, exclusive=exclusive)(
            handler
        )
        return handler

    def event(self, event: str):
        raise NotImplementedError
