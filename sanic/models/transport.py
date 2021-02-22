import sys

from typing import Union


if sys.version_info < (3, 8):
    from asyncio import BaseTransport

    from sanic.models.asgi import MockTransport

    TransportProtocol = Union[MockTransport, BaseTransport]
else:
    # Protocol is a 3.8+ feature
    from typing import Protocol

    class TransportProtocol(Protocol):
        def get_protocol(self):
            ...

        def get_extra_info(self, info: str) -> Union[str, bool, None]:
            ...
