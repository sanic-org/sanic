import asyncio
import json as stdjson

from collections import namedtuple
from textwrap import dedent
from typing import AnyStr

import pytest

from sanic_testing.reusable import ReusableClient

from sanic import json, text
from sanic.app import Sanic


PORT = 1234


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


@pytest.fixture
def test_app(app: Sanic):
    app.config.KEEP_ALIVE_TIMEOUT = 1

    @app.get("/")
    async def base_handler(request):
        return text("111122223333444455556666777788889999")

    @app.post("/upload", stream=True)
    async def upload_handler(request):
        data = [part.decode("utf-8") async for part in request.stream]
        return json(data)

    return app


@pytest.fixture
def runner(test_app):
    client = ReusableClient(test_app, port=PORT)
    client.run()
    yield client
    client.stop()


@pytest.fixture
def client(runner):
    client = namedtuple("Client", ("raw", "send", "recv"))

    raw = RawClient(runner.host, runner.port)
    runner._run(raw.connect())

    def send(msg):
        nonlocal runner
        nonlocal raw
        runner._run(raw.send(msg))

    def recv(**kwargs):
        nonlocal runner
        nonlocal raw
        method = raw.recv_until if "until" in kwargs else raw.recv
        return runner._run(method(**kwargs))

    yield client(raw, send, recv)

    runner._run(raw.close())


def test_full_message(client):
    client.send(
        """
        GET / HTTP/1.1
        host: localhost:7777

        """
    )
    response = client.recv()
    assert len(response) == 140
    assert b"200 OK" in response


def test_transfer_chunked(client):
    client.send(
        """
        POST /upload HTTP/1.1
        transfer-encoding: chunked

        """
    )
    client.send(b"3\r\nfoo\r\n")
    client.send(b"3\r\nbar\r\n")
    client.send(b"0\r\n\r\n")
    response = client.recv()
    _, body = response.rsplit(b"\r\n\r\n", 1)
    data = stdjson.loads(body)

    assert data == ["foo", "bar"]
