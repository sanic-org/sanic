from typing import Set

from sanic_routing.exceptions import NotFound

from sanic.handlers import SignalHandler
from sanic.models.futures import FutureSignal
from sanic.signals import Signal


class SignalMixin:
    def __init__(self, *args, **kwargs) -> None:
        self._future_signals: Set[FutureSignal] = set()

    def signal(
        self,
        event: str,
        apply: bool = True,
    ):
        # TODO:
        # - Event validation

        def decorator(handler: SignalHandler):
            nonlocal event
            nonlocal apply

            future_signal = FutureSignal(handler, event)
            self._future_signals.add(future_signal)

            if apply:
                self._apply_signal(future_signal)

            return future_signal

        return decorator

    def event(self, event):
        signal = self.signal_router.name_index.get(event)
        if not signal:
            raise NotFound
        return signal.ctx.event.wait()
