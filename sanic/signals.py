import typing as t

from inspect import iscoroutinefunction
from asyncio import AbstractEventLoop
from frozenlist import FrozenList

import sanic


from sanic.exceptions import SignalsNotFrozenException


class Singleton(type):
    _instances = {}  # type: t.Dict[type, t.Any]

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(
                *args, **kwargs
            )
        return cls._instances[cls]


class SignalContext:
    __slots__ = ["_namespace", "_context", "_action"]

    def __init__(
        self,
        namespace: t.AnyStr,
        context: t.AnyStr,
        action: t.Union[None, t.AnyStr],
    ):
        self._namespace = namespace  # type: t.AnyStr
        self._context = context  # type: t.AnyStr
        self._action = action  # type: t.Union[None, t.AnyStr]

    def __repr__(self):
        signal_name = f"{self._namespace}.{self._context}"
        if self._action:
            signal_name = f"{signal_name}.{self._action}"
        return signal_name


class SignalData:
    __slots__ = ["_request", "_response", "_additional_info"]

    def __init__(
        self,
        request: t.Union[None, "sanic.request.Request"] = None,
        response: t.Union[None, "sanic.response.HTTPResponse"] = None,
        additional_info: t.Dict[t.AnyStr, t.Any] = None,
    ):
        self._request = request  # type: t.Union[None, "sanic.request.Request"]
        self._response = (
            response
        )  # type: t.Union[None, "sanic.response.HTTPResponse"]
        self._additional_info = (
            additional_info
        )  # type: t.Dict[t.AnyStr, t.Any]

    @property
    def request(self) -> t.Union[None, "sanic.request.Request"]:
        return self._request

    @property
    def response(self) -> t.Union[None, "sanic.response.HTTPResponse"]:
        return self._response

    @property
    def additional_info(self) -> t.Dict[t.AnyStr, t.Any]:
        return self._additional_info

    def __repr__(self):
        info = ""
        if self._request:
            info = f"\nRequest(method={self._request.method},url={self._request.url})"

        if self._response:
            info = f"{info}\nResponse(status={self._response.status})"

        if self._additional_info:
            info = f"{info}\nAdditional Info({self._additional_info})"

        return info


class Signal(FrozenList):
    __slots__ = ("_owner",)

    def __init__(self, owner):
        super(Signal, self).__init__(items=None)
        self._owner = owner

    async def dispatch(
        self,
        signal: SignalContext,
        app: t.Union[None, "sanic.Sanic"],
        loop: t.Union[None, AbstractEventLoop],
        signal_data: t.Union[None, SignalData],
    ) -> None:
        if not self.frozen:
            raise SignalsNotFrozenException(
                message=f"Unable to dispatch events on a non-frozen signal set for source {self._owner}"
            )

        for recipient in self:
            if iscoroutinefunction(recipient):
                await recipient(app, loop, signal, signal_data)
            else:
                recipient(app, loop, signal, signal_data)


signal_handler = t.Callable[
    [
        "sanic.Sanic",
        AbstractEventLoop,
        SignalContext,
        t.Union[None, SignalData],
    ],
    t.Union[None, t.Awaitable[None]],
]


class SignalRegistry(metaclass=Singleton):
    def __init__(self):
        self._signals_map = {}  # type: t.Dict[SignalContext, Signal]

    @property
    def signals(self) -> t.Dict[SignalContext, Signal]:
        return self._signals_map

    def register(self, context: SignalContext, owner: t.AnyStr) -> None:
        self._signals_map[context] = Signal(owner=owner)

    def subscribe(
        self, context: SignalContext, callback: t.Callable[..., signal_handler]
    ) -> None:
        self._signals_map[context].append(callback)

    async def dispatch(
        self,
        context: SignalContext,
        data: t.Union[None, SignalData] = None,
        app: t.Union[None, "sanic.Sanic"] = None,
        loop: t.Union[None, AbstractEventLoop] = None,
    ) -> None:
        await self._signals_map[context].dispatch(
            app=app, loop=loop, signal=context, signal_data=data
        )

    def freeze(self, context: t.Union[SignalContext, None] = None) -> None:
        if not context:
            for _ctx, _sig in self._signals_map.items():
                _sig.freeze()
        else:
            self._signals_map[context].freeze()
