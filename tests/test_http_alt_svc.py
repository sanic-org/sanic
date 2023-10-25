import sys
from pathlib import Path

import pytest

from sanic.app import Sanic
from sanic.response import empty
from tests.client import RawClient

parent_dir = Path(__file__).parent
localhost_dir = parent_dir / "certs/localhost"

PORT = 12344


@pytest.mark.skipif(sys.version_info < (3, 9), reason="Not supported in 3.8")
def test_http1_response_has_alt_svc():
    """Verify that H1 server returns alt-svc header when H3 is also running."""
    app = Sanic("TestAltSvc")
    response = b""

    @app.get("/")
    async def handler(*_):
        return empty()

    @app.after_server_start
    async def do_request(*_):
        nonlocal response

        client = RawClient(app.state.host, app.state.port)
        await client.connect()
        await client.send(
            """
            GET / HTTP/1.0
            host: localhost:7777

            """
        )
        response = await client.recv()
        await client.close()
        app.stop()

    app.prepare(
        version=3,
        ssl={
            "cert": localhost_dir / "fullchain.pem",
            "key": localhost_dir / "privkey.pem",
        },
        port=PORT,
    )
    app.prepare(
        version=1,
        port=PORT,
    )
    Sanic.serve_single()

    assert f'alt-svc: h3=":{PORT}"\r\n'.encode() in response
