from aiosignal import Signal
from typing import Dict, List

class SignalData:
    __slots__ = (
        "context", "exception", "additional_info", "request", "response", "namespace",  "name"
    )

    def __init__(self, context, exception=None, request=None, response=None, additional_info=None):
        self.context: str = context
        self.exception: Exception = exception
        self.additional_info: dict = additional_info
        self.request = request
        self.response = response


class Namespace:
    def __init__(self, namespace, owner):
        self._namespace = namespace  # type: str
        self._owner = owner
        self._signals: Dict[str, Dict[str, Signal]] = {}

    def signal(self, context, action):
        try:
            self._signals[context]
        except KeyError:
            self._signals[context] = {}

        try:
            self._signals[context][action].append(Signal(owner=self._owner))
        except KeyError:
            self._signals[context][action] = Signal(owner=self._owner)

    def subscribe(self, context, action, callback):
        try:
            self._signals[context][action].append(callback)
        except KeyError:
            self.signal(context, action)
            self._signals[context][action].append(callback)

    async def publish(self, context, action, data: SignalData = None):
        if not data:
            data = {}
        data.namespace = self._namespace
        data.context = context
        data.action = action
        await self._signals[context][action].send(data=data)

    def freeze(self):
        for _, context_map in self._signals.items():
            for _, signal in context_map.items():
                signal.freeze()
