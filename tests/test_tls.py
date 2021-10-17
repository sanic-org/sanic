import logging
import os
import ssl
import uuid

from urllib.parse import urlparse

import pytest

from sanic_testing.testing import HOST, PORT, SanicTestClient

from sanic import Sanic
from sanic.compat import OS_IS_WINDOWS
from sanic.log import logger
from sanic.response import text


current_dir = os.path.dirname(os.path.realpath(__file__))
localhost_cert = os.path.join(current_dir, "certs/localhost/fullchain.pem")
localhost_key = os.path.join(current_dir, "certs/localhost/privkey.pem")
sanic_cert = os.path.join(current_dir, "certs/sanic.example/fullchain.pem")
sanic_key = os.path.join(current_dir, "certs/sanic.example/privkey.pem")


@pytest.mark.parametrize(
    "path,query,expected_url",
    [
        ("/foo", "", "https://{}:{}/foo"),
        ("/bar/baz", "", "https://{}:{}/bar/baz"),
        ("/moo/boo", "arg1=val1", "https://{}:{}/moo/boo?arg1=val1"),
    ],
)
def test_url_attributes_with_ssl_context(app, path, query, expected_url):
    context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(localhost_cert, localhost_key)

    async def handler(request):
        return text("OK")

    app.add_route(handler, path)

    port = app.test_client.port
    request, response = app.test_client.get(
        f"https://{HOST}:{PORT}" + path + f"?{query}",
        server_kwargs={"ssl": context},
    )
    assert request.url == expected_url.format(HOST, request.server_port)

    parsed = urlparse(request.url)

    assert parsed.scheme == request.scheme
    assert parsed.path == request.path
    assert parsed.query == request.query_string
    assert parsed.netloc == request.host


@pytest.mark.parametrize(
    "path,query,expected_url",
    [
        ("/foo", "", "https://{}:{}/foo"),
        ("/bar/baz", "", "https://{}:{}/bar/baz"),
        ("/moo/boo", "arg1=val1", "https://{}:{}/moo/boo?arg1=val1"),
    ],
)
def test_url_attributes_with_ssl_dict(app, path, query, expected_url):
    ssl_dict = {"cert": localhost_cert, "key": localhost_key}

    async def handler(request):
        return text("OK")

    app.add_route(handler, path)

    request, response = app.test_client.get(
        f"https://{HOST}:{PORT}" + path + f"?{query}",
        server_kwargs={"ssl": ssl_dict},
    )
    assert request.url == expected_url.format(HOST, request.server_port)

    parsed = urlparse(request.url)

    assert parsed.scheme == request.scheme
    assert parsed.path == request.path
    assert parsed.query == request.query_string
    assert parsed.netloc == request.host


def test_invalid_ssl_dict(app):
    @app.get("/test")
    async def handler(request):
        return text("ssl test")

    ssl_dict = {"cert": None, "key": None}

    with pytest.raises(ValueError) as excinfo:
        request, response = app.test_client.get(
            "/test", server_kwargs={"ssl": ssl_dict}
        )

    assert str(excinfo.value) == "SSL dict needs filenames for cert and key."


@pytest.mark.skipif(
    OS_IS_WINDOWS and sys.version_info >= (3, 8),
    reason="Not testable with current client",
)
def test_logger_static_and_secure(caplog):
    # Same as test_logger, except for more coverage:
    # - test_client initialised separately for static port
    # - using ssl
    rand_string = str(uuid.uuid4())

    app = Sanic(name=__name__)

    @app.get("/")
    def log_info(request):
        logger.info(rand_string)
        return text("hello")

    ssl_dict = {"cert": localhost_cert, "key": localhost_key}

    test_client = SanicTestClient(app, port=42101)
    with caplog.at_level(logging.INFO):
        request, response = test_client.get(
            f"https://127.0.0.1:{test_client.port}/",
            server_kwargs=dict(ssl=ssl_dict),
        )

    port = test_client.port

    assert caplog.record_tuples[0] == (
        "sanic.root",
        logging.INFO,
        f"Goin' Fast @ https://127.0.0.1:{port}",
    )
    assert caplog.record_tuples[1] == (
        "sanic.root",
        logging.INFO,
        f"https://127.0.0.1:{port}/",
    )
    assert caplog.record_tuples[2] == ("sanic.root", logging.INFO, rand_string)
    assert caplog.record_tuples[-1] == (
        "sanic.root",
        logging.INFO,
        "Server Stopped",
    )
