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
localhost_dir = os.path.join(current_dir, "certs/localhost")
sanic_dir = os.path.join(current_dir, "certs/sanic.example")
invalid_dir = os.path.join(current_dir, "certs/invalid.nonexist")
localhost_cert = os.path.join(localhost_dir, "fullchain.pem")
localhost_key = os.path.join(localhost_dir, "privkey.pem")
sanic_cert = os.path.join(sanic_dir, "fullchain.pem")
sanic_key = os.path.join(sanic_dir, "privkey.pem")


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


def test_cert_sni(app):
    ssl_list = [localhost_dir, sanic_dir]

    @app.get("/test")
    async def handler(request):
        return text(request.conn_info.server_name)

    port = app.test_client.port
    request, response = app.test_client.get(
        f"https://localhost:{port}/test",
        server_kwargs={"ssl": ssl_list},
    )
    assert response.status == 200
    assert response.text == "localhost"

    """The following requires foo.sanic.test 127.0.0.1 in hosts
    port = app.test_client.port
    request, response = app.test_client.get(
        f"https://foo.sanic.test:{port}/test",
        server_kwargs={"ssl": ssl_list},
    )
    assert response.status == 200
    assert response.text == "foo.sanic.test"
    """


def test_missing_sni(app):
    """The sanic cert does not list 127.0.0.1 and httpx does not send IP as SNI anyway."""
    ssl_list = [sanic_dir]

    @app.get("/")
    async def handler(request):
        return text(request.conn_info.server_name)

    port = app.test_client.port
    with pytest.raises(Exception) as exc:
        request, response = app.test_client.get(
            f"https://127.0.0.1:{port}/",
            server_kwargs={"ssl": ssl_list},
        )

    assert "Request and response object expected" in str(exc.value)


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


def test_invalid_ssl_type(app):
    @app.get("/test")
    async def handler(request):
        return text("ssl test")

    with pytest.raises(ValueError) as excinfo:
        request, response = app.test_client.get(
            "/test", server_kwargs={"ssl": False}
        )

    assert "Invalid ssl argument" in str(excinfo.value)


def test_cert_file_on_pathlist(app):
    @app.get("/test")
    async def handler(request):
        return text("ssl test")

    ssl_list = [sanic_cert]

    with pytest.raises(ValueError) as excinfo:
        request, response = app.test_client.get(
            "/test", server_kwargs={"ssl": ssl_list}
        )

    assert "folder expected" in str(excinfo.value)
    assert sanic_cert in str(excinfo.value)


def test_missing_cert_path(app):
    @app.get("/test")
    async def handler(request):
        return text("ssl test")

    ssl_list = [invalid_dir]

    with pytest.raises(ValueError) as excinfo:
        request, response = app.test_client.get(
            "/test", server_kwargs={"ssl": ssl_list}
        )

    assert "not found" in str(excinfo.value)
    assert invalid_dir + "/privkey.pem" in str(excinfo.value)


def test_missing_cert_file(app):
    @app.get("/test")
    async def handler(request):
        return text("ssl test")

    invalid2 = invalid_dir.replace("nonexist", "certmissing")
    ssl_list = [invalid2]

    with pytest.raises(ValueError) as excinfo:
        request, response = app.test_client.get(
            "/test", server_kwargs={"ssl": ssl_list}
        )

    assert "not found" in str(excinfo.value)
    assert invalid2 + "/fullchain.pem" in str(excinfo.value)


def test_logger_vhosts(caplog):
    app = Sanic(name=__name__)

    @app.after_server_start
    def stop(*args):
        app.stop()

    with caplog.at_level(logging.INFO):
        app.run(host="127.0.0.1", port=42102, ssl=[localhost_dir, sanic_dir])

    logmsg = [m for s, l, m in caplog.record_tuples if m.startswith('Certificate')][0]

    assert logmsg == (
        "Certificate vhosts: localhost, 127.0.0.1, 0:0:0:0:0:0:0:1, sanic.example, www.sanic.example, *.sanic.test, 2001:DB8:0:0:0:0:0:541C, localhost"
    )


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
