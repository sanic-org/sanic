import json as stdjson

from collections import namedtuple
from pathlib import Path
from sys import version_info

import pytest

from sanic_testing.reusable import ReusableClient

from sanic import json, text
from sanic.app import Sanic
from tests.client import RawClient


parent_dir = Path(__file__).parent
localhost_dir = parent_dir / "certs/localhost"


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
def runner(test_app: Sanic, port):
    client = ReusableClient(test_app, port=port)
    client.run()
    yield client
    client.stop()


@pytest.fixture
def client(runner: ReusableClient):
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

    # AltSvcCheck touchup removes the Alt-Svc header from the
    # response in the Python 3.9+ in this case
    assert len(response) == (151 if version_info < (3, 9) else 140)
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


def test_url_encoding(client):
    client.send(
        """
        GET /invalid\xa0url HTTP/1.1

        """
    )
    response = client.recv()
    headers, body = response.rsplit(b"\r\n\r\n", 1)

    assert b"400 Bad Request" in headers
    assert b"URL may only contain US-ASCII characters." in body


@pytest.mark.parametrize(
    "content_length",
    (
        b"-50",
        b"+50",
        b"5_0",
        b"50.5",
    ),
)
def test_invalid_content_length(content_length, client):
    body = b"Hello" * 10
    client.send(
        b"POST /upload HTTP/1.1\r\n"
        + b"content-length: "
        + content_length
        + b"\r\n\r\n"
        + body
        + b"\r\n\r\n"
    )

    response = client.recv()
    headers, body = response.rsplit(b"\r\n\r\n", 1)

    assert b"400 Bad Request" in headers
    assert b"Bad content-length" in body


@pytest.mark.parametrize(
    "chunk_length",
    (
        b"-50",
        b"+50",
        b"5_0",
        b"50.5",
    ),
)
def test_invalid_chunk_length(chunk_length, client):
    body = b"Hello" * 10
    client.send(
        b"POST /upload HTTP/1.1\r\n"
        + b"transfer-encoding: chunked\r\n\r\n"
        + chunk_length
        + b"\r\n"
        + body
        + b"\r\n"
        + b"0\r\n\r\n"
    )

    response = client.recv()
    headers, body = response.rsplit(b"\r\n\r\n", 1)

    assert b"400 Bad Request" in headers
    assert b"Bad chunked encoding" in body


def test_smuggle(client):
    client.send(
        """
        POST /upload HTTP/1.1
        Content-Length: 5
        Transfer-Encoding: chunked
        Transfer-Encoding: xchunked

        5
        hello
        0

        GET / HTTP/1.1
        
        """  # noqa
    )

    response = client.recv()
    num_responses = response.count(b"HTTP/1.1")
    assert num_responses == 1

    headers, body = response.rsplit(b"\r\n\r\n", 1)
    assert b"400 Bad Request" in headers
    assert b"Bad Request" in body
