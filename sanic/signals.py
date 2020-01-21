from aiosignal import Signal
from typing import Dict, List
from sanic.request import Request
from sanic.response import HTTPResponse


class SignalData:
    __slots__ = (
        "context", "exception", "additional_info", "request", "response", "namespace",  "name"
    )

    def __init__(self, context, exception=None, request=None, response=None, additional_info=None):
        self.context: str = context
        self.exception: Exception = exception
        self.additional_info: dict = additional_info
        self.request: Request = request
        self.response: HTTPResponse = response


class Namespace:
    def __init__(self, namespace):
        self._namespace = namespace  # type: str
        self._signals: Dict[str, Signal] = {}

    def signal(self, name, owner):
        try:
            self._signals[name].append(Signal(owner=owner))
        except KeyError:
            self._signals[name] = Signal(owner=owner)

    def register(self, name, callback):
        self._signals[name].append(callback)

    async def publish(self, name, data: SignalData = None):
        if not data:
            data = {}
        data.namespace = self._namespace
        data.name = name
        await self._signals[name].send(data=data)

    def freeze(self):
        for key, signal in self._signals.items():
            signal.freeze()
