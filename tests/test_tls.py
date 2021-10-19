import logging
import os
import ssl
import uuid

from contextlib import contextmanager
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


@contextmanager
def replace_server_name(hostname):
    """Temporarily replace the server name sent with all TLS requests with a fake hostname."""

    def hack_wrap_bio(
        self,
        incoming,
        outgoing,
        server_side=False,
        server_hostname=None,
        session=None,
    ):
        return orig_wrap_bio(
            self, incoming, outgoing, server_side, hostname, session
        )

    orig_wrap_bio, ssl.SSLContext.wrap_bio = (
        ssl.SSLContext.wrap_bio,
        hack_wrap_bio,
    )
    try:
        yield
    finally:
        ssl.SSLContext.wrap_bio = orig_wrap_bio


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
    ssl_list = [sanic_dir, localhost_dir]

    @app.get("/sni")
    async def handler(request):
        return text(request.conn_info.server_name)

    @app.get("/commonname")
    async def handler(request):
        return text(request.conn_info.cert.get("commonName"))

    # This test should match the localhost cert
    port = app.test_client.port
    request, response = app.test_client.get(
        f"https://localhost:{port}/sni",
        server_kwargs={"ssl": ssl_list},
    )
    assert response.status == 200
    assert response.text == "localhost"

    request, response = app.test_client.get(
        f"https://localhost:{port}/commonname",
        server_kwargs={"ssl": ssl_list},
    )
    assert response.status == 200
    assert response.text == "localhost"

    # This part should use the sanic.example cert because it matches
    with replace_server_name("www.sanic.example"):
        request, response = app.test_client.get(
            f"https://127.0.0.1:{port}/sni",
            server_kwargs={"ssl": ssl_list},
        )
        assert response.status == 200
        assert response.text == "www.sanic.example"

        request, response = app.test_client.get(
            f"https://127.0.0.1:{port}/commonname",
            server_kwargs={"ssl": ssl_list},
        )
        assert response.status == 200
        assert response.text == "sanic.example"

    # This part should use the sanic.example cert, that being the first listed
    with replace_server_name("invalid.test"):
        request, response = app.test_client.get(
            f"https://127.0.0.1:{port}/sni",
            server_kwargs={"ssl": ssl_list},
        )
        assert response.status == 200
        assert response.text == "invalid.test"

        request, response = app.test_client.get(
            f"https://127.0.0.1:{port}/commonname",
            server_kwargs={"ssl": ssl_list},
        )
        assert response.status == 200
        assert response.text == "sanic.example"


def test_missing_sni(app):
    """The sanic cert does not list 127.0.0.1 and httpx does not send IP as SNI anyway."""
    ssl_list = [None, sanic_dir]

    @app.get("/sni")
    async def handler(request):
        return text(request.conn_info.server_name)

    port = app.test_client.port
    with pytest.raises(Exception) as exc:
        request, response = app.test_client.get(
            f"https://127.0.0.1:{port}/sni",
            server_kwargs={"ssl": ssl_list},
        )
    assert "Request and response object expected" in str(exc.value)


def test_no_matching_cert(app):
    """The sanic cert does not list 127.0.0.1 and httpx does not send IP as SNI anyway."""
    ssl_list = [None, sanic_dir]

    @app.get("/sni")
    async def handler(request):
        return text(request.conn_info.server_name)

    port = app.test_client.port
    with replace_server_name("invalid.test"):
        with pytest.raises(Exception) as exc:
            request, response = app.test_client.get(
                f"https://127.0.0.1:{port}/sni",
                server_kwargs={"ssl": ssl_list},
            )
    assert "Request and response object expected" in str(exc.value)


def test_wildcards(app):
    ssl_list = [None, localhost_dir, sanic_dir]

    @app.get("/sni")
    async def handler(request):
        return text(request.conn_info.server_name)

    port = app.test_client.port

    with replace_server_name("foo.sanic.test"):
        request, response = app.test_client.get(
            f"https://127.0.0.1:{port}/sni",
            server_kwargs={"ssl": ssl_list},
        )
        assert response.status == 200
        assert response.text == "foo.sanic.test"

    with replace_server_name("sanic.test"):
        with pytest.raises(Exception) as exc:
            request, response = app.test_client.get(
                f"https://127.0.0.1:{port}/sni",
                server_kwargs={"ssl": ssl_list},
            )
        assert "Request and response object expected" in str(exc.value)
    with replace_server_name("sub.foo.sanic.test"):
        with pytest.raises(Exception) as exc:
            request, response = app.test_client.get(
                f"https://127.0.0.1:{port}/sni",
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


def test_no_certs_on_list(app):
    @app.get("/test")
    async def handler(request):
        return text("ssl test")

    ssl_list = [None]

    with pytest.raises(ValueError) as excinfo:
        request, response = app.test_client.get(
            "/test", server_kwargs={"ssl": ssl_list}
        )

    assert "No certificates" in str(excinfo.value)


def test_logger_vhosts(caplog):
    app = Sanic(name=__name__)

    @app.after_server_start
    def stop(*args):
        app.stop()

    with caplog.at_level(logging.INFO):
        app.run(host="127.0.0.1", port=42102, ssl=[localhost_dir, sanic_dir])

    logmsg = [
        m for s, l, m in caplog.record_tuples if m.startswith("Certificate")
    ][0]

    assert logmsg == (
        "Certificate vhosts: localhost, 127.0.0.1, 0:0:0:0:0:0:0:1, sanic.example, www.sanic.example, *.sanic.test, 2001:DB8:0:0:0:0:0:541C"
    )
