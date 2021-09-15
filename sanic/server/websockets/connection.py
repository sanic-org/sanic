from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    MutableMapping,
    Optional,
    Union,
)


ASIMessage = MutableMapping[str, Any]


class WebSocketConnection:
    """
    This is for ASGI Connections.
    It provides an interface similar to WebsocketProtocol, but
    sends/receives over an ASGI connection.
    """

    # TODO
    # - Implement ping/pong

    def __init__(
        self,
        send: Callable[[ASIMessage], Awaitable[None]],
        receive: Callable[[], Awaitable[ASIMessage]],
        subprotocols: Optional[List[str]] = None,
    ) -> None:
        self._send = send
        self._receive = receive
        self._subprotocols = subprotocols or []

    async def send(self, data: Union[str, bytes], *args, **kwargs) -> None:
        message: Dict[str, Union[str, bytes]] = {"type": "websocket.send"}

        if isinstance(data, bytes):
            message.update({"bytes": data})
        else:
            message.update({"text": str(data)})

        await self._send(message)

    async def recv(self, *args, **kwargs) -> Optional[str]:
        message = await self._receive()

        if message["type"] == "websocket.receive":
            return message["text"]
        elif message["type"] == "websocket.disconnect":
            pass

        return None

    receive = recv

    async def accept(self, subprotocols: Optional[List[str]] = None) -> None:
        subprotocol = None
        if subprotocols:
            for subp in subprotocols:
                if subp in self.subprotocols:
                    subprotocol = subp
                    break

        await self._send(
            {
                "type": "websocket.accept",
                "subprotocol": subprotocol,
            }
        )

    async def close(self, code: int = 1000, reason: str = "") -> None:
        pass

    @property
    def subprotocols(self):
        return self._subprotocols

    @subprotocols.setter
    def subprotocols(self, subprotocols: Optional[List[str]] = None):
        self._subprotocols = subprotocols or []
