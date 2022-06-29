import asyncio

from textwrap import dedent
from typing import AnyStr


class RawClient:
    CRLF = b"\r\n"

    def __init__(self, host: str, port: int):
        self.reader = None
        self.writer = None
        self.host = host
        self.port = port

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(
            self.host, self.port
        )

    async def close(self):
        self.writer.close()
        await self.writer.wait_closed()

    async def send(self, message: AnyStr):
        if isinstance(message, str):
            msg = self._clean(message).encode("utf-8")
        else:
            msg = message
        await self._send(msg)

    async def _send(self, message: bytes):
        if not self.writer:
            raise Exception("No open write stream")
        self.writer.write(message)

    async def recv(self, nbytes: int = -1) -> bytes:
        if not self.reader:
            raise Exception("No open read stream")
        return await self.reader.read(nbytes)

    def _clean(self, message: str) -> str:
        return (
            dedent(message)
            .lstrip("\n")
            .replace("\n", self.CRLF.decode("utf-8"))
        )
