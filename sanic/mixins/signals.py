import typing as t

from sanic.exceptions import InvalidSignalFormatException
from sanic.signals import SignalRegistry, SignalContext
from sanic.utils import Singleton


class SignalMixin:
    __metaclass__ = Singleton

    def __init__(self, *args, **kwargs) -> None:
        self._signal_registry = SignalRegistry()
        self._ctx_mapper = {}  # type: t.Dict[str, SignalContext]
        self.name = ""

    def signal(self, signal: str):
        def _wrapper(handler: t.Callable):
            parts = signal.split(".")
            if len(parts) < 2 or len(parts) > 3:
                raise InvalidSignalFormatException(
                    message=f"Signal format {signal} is invalid. Supported format is <namespace>.<context>[.<action>]"
                )
            else:
                if not self._ctx_mapper.get(signal):
                    ctx = SignalContext(
                        namespace=parts[0],
                        context=parts[1],
                        action=parts[2] if len(parts) > 2 else None,
                    )
                    self._ctx_mapper[signal] = ctx
                    self._signal_registry.register(
                        context=ctx, owner=self.name
                    )
                else:
                    ctx = self._ctx_mapper[signal]
                self._signal_registry.subscribe(context=ctx, callback=handler)
            return handler

        return _wrapper

    def get_signal_context(self, signal: str) -> t.Union[None, SignalContext]:
        return self._ctx_mapper.get(signal)

    def freeze(self, signal: t.Union[None, str] = None):
        self._signal_registry.freeze(
            context=self._ctx_mapper[signal] if signal else None
        )

    async def publish(self, signal: str, data: t.Dict[str, t.Any]):
        raise NotImplementedError
