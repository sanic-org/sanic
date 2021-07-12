import asyncio

from collections import namedtuple
from textwrap import dedent

import pytest
import ujson

from sanic_testing.reusable import ReusableClient

from sanic import json, text
from sanic.app import Sanic


PORT = 1234


class RawClient:
    CRLF = b"\r\n"

    def __init__(self, host: str, port: int, loop: asyncio.BaseEventLoop):
        self.reader = None
        self.writer = None
        self.host = host
        self.port = port
        self.loop = loop

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(
            self.host, self.port, loop=self.loop
        )

    async def close(self):
        self.writer.close()
        await self.writer.wait_closed()

    async def send(self, message: bytes):
        msg = self._clean(message)
        await self._send(msg)

    async def _send(self, message: bytes):
        if not self.writer:
            raise Exception("No open write stream")
        self.writer.write(message)

    async def recv(self, nbytes: int = -1) -> bytes:
        if not self.reader:
            raise Exception("No open read stream")
        return await self.reader.read(nbytes)

    def _clean(self, message: bytes) -> bytes:
        return (
            dedent(message.decode("utf-8"))
            .lstrip()
            .encode("utf-8")
            .replace(b"\n", self.CRLF)
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

    loop = runner._loop
    raw = RawClient(runner.host, runner.port, loop)
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
        b"""
        GET / HTTP/1.1
        host: localhost:7777

        """
    )
    response = client.recv()
    assert len(response) == 140
    assert b"200 OK" in response


def test_transfer_chunked(client):
    client.send(
        b"""
        POST /upload HTTP/1.1
        transfer-encoding: chunked

        """
    )
    client.send(b"3\nfoo\n")
    client.send(b"3\nfoo\n")
    client.send(b"0\n\n")
    response = client.recv()
    _, body = response.rsplit(b"\r\n\r\n", 1)
    json = ujson.loads(body)

    assert json == ["foo", "foo"]
