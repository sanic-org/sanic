from asyncio.futures import Future
from typing import Any, Callable, Dict, Set, Tuple

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
        event: str,
        *,
        apply: bool = True,
        where: Dict[str, Any] = None,
    ) -> Callable[[SignalHandler], FutureSignal]:
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
        :param where: For use with the ``where`` argument in dispatch
            filtering, defaults to None
        :type where: Dict[str, Any], optional
        """

        def decorator(handler: SignalHandler):
            nonlocal event
            nonlocal apply

            future_signal = FutureSignal(
                handler, event, HashableDict(where or {})
            )
            self._future_signals.add(future_signal)

            if apply:
                self._apply_signal(future_signal)

            return future_signal

        return decorator

    def event(
        self, event: str
    ) -> Future[Tuple[Set[Future[Any]], Set[Future[Any]]]]:
        raise NotImplementedError
