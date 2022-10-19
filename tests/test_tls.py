import logging
import os
import ssl
import subprocess

from contextlib import contextmanager
from multiprocessing import Event
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.parse import urlparse

import pytest

from sanic_testing.testing import HOST, PORT

import sanic.http.tls.creators

from sanic import Sanic
from sanic.application.constants import Mode
from sanic.constants import LocalCertCreator
from sanic.exceptions import SanicException
from sanic.helpers import _default
from sanic.http.tls.context import SanicSSLContext
from sanic.http.tls.creators import (
    MkcertCreator,
    TrustmeCreator,
    get_ssl_context,
)
from sanic.response import text


current_dir = os.path.dirname(os.path.realpath(__file__))
localhost_dir = os.path.join(current_dir, "certs/localhost")
sanic_dir = os.path.join(current_dir, "certs/sanic.example")
invalid_dir = os.path.join(current_dir, "certs/invalid.nonexist")
localhost_cert = os.path.join(localhost_dir, "fullchain.pem")
localhost_key = os.path.join(localhost_dir, "privkey.pem")
sanic_cert = os.path.join(sanic_dir, "fullchain.pem")
sanic_key = os.path.join(sanic_dir, "privkey.pem")


@pytest.fixture
def server_cert():
    return Mock()


@pytest.fixture
def issue_cert(server_cert):
    mock = Mock(return_value=server_cert)
    return mock


@pytest.fixture
def ca(issue_cert):
    ca = Mock()
    ca.issue_cert = issue_cert
    return ca


@pytest.fixture
def trustme(ca):
    module = Mock()
    module.CA = Mock(return_value=ca)
    return module


@pytest.fixture
def MockMkcertCreator():
    class Creator(MkcertCreator):
        SUPPORTED = True

        def check_supported(self):
            if not self.SUPPORTED:
                raise SanicException("Nope")

        generate_cert = Mock()

    return Creator


@pytest.fixture
def MockTrustmeCreator():
    class Creator(TrustmeCreator):
        SUPPORTED = True

        def check_supported(self):
            if not self.SUPPORTED:
                raise SanicException("Nope")

        generate_cert = Mock()

    return Creator


@contextmanager
def replace_server_name(hostname):
    """Temporarily replace the server name sent with all TLS requests with
    a fake hostname."""

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

    request, _ = app.test_client.get(
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

    request, _ = app.test_client.get(
        f"https://{HOST}:{PORT}" + path + f"?{query}",
        server_kwargs={"ssl": ssl_dict},
    )
    assert request.url == expected_url.format(HOST, request.server_port)

    parsed = urlparse(request.url)

    assert parsed.scheme == request.scheme
    assert parsed.path == request.path
    assert parsed.query == request.query_string
    assert parsed.netloc == request.host


def test_cert_sni_single(app):
    @app.get("/sni")
    async def handler1(request):
        return text(request.conn_info.server_name)

    @app.get("/commonname")
    async def handler2(request):
        return text(request.conn_info.cert.get("commonName"))

    port = app.test_client.port
    _, response = app.test_client.get(
        f"https://localhost:{port}/sni",
        server_kwargs={"ssl": localhost_dir},
    )
    assert response.status == 200
    assert response.text == "localhost"

    _, response = app.test_client.get(
        f"https://localhost:{port}/commonname",
        server_kwargs={"ssl": localhost_dir},
    )
    assert response.status == 200
    assert response.text == "localhost"


def test_cert_sni_list(app):
    ssl_list = [sanic_dir, localhost_dir]

    @app.get("/sni")
    async def handler1(request):
        return text(request.conn_info.server_name)

    @app.get("/commonname")
    async def handler2(request):
        return text(request.conn_info.cert.get("commonName"))

    # This test should match the localhost cert
    port = app.test_client.port
    _, response = app.test_client.get(
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
        _, response = app.test_client.get(
            f"https://127.0.0.1:{port}/sni",
            server_kwargs={"ssl": ssl_list},
        )
        assert response.status == 200
        assert response.text == "www.sanic.example"

        _, response = app.test_client.get(
            f"https://127.0.0.1:{port}/commonname",
            server_kwargs={"ssl": ssl_list},
        )
        assert response.status == 200
        assert response.text == "sanic.example"

    # This part should use the sanic.example cert, that being the first listed
    with replace_server_name("invalid.test"):
        _, response = app.test_client.get(
            f"https://127.0.0.1:{port}/sni",
            server_kwargs={"ssl": ssl_list},
        )
        assert response.status == 200
        assert response.text == "invalid.test"

        _, response = app.test_client.get(
            f"https://127.0.0.1:{port}/commonname",
            server_kwargs={"ssl": ssl_list},
        )
        assert response.status == 200
        assert response.text == "sanic.example"


def test_missing_sni(app):
    """The sanic cert does not list 127.0.0.1 and httpx does not send
    IP as SNI anyway."""
    ssl_list = [None, sanic_dir]

    @app.get("/sni")
    async def handler(request):
        return text(request.conn_info.server_name)

    port = app.test_client.port
    with pytest.raises(Exception) as exc:
        app.test_client.get(
            f"https://127.0.0.1:{port}/sni",
            server_kwargs={"ssl": ssl_list},
        )
    assert "Request and response object expected" in str(exc.value)


def test_no_matching_cert(app):
    """The sanic cert does not list 127.0.0.1 and httpx does not send
    IP as SNI anyway."""
    ssl_list = [None, sanic_dir]

    @app.get("/sni")
    async def handler(request):
        return text(request.conn_info.server_name)

    port = app.test_client.port
    with replace_server_name("invalid.test"):
        with pytest.raises(Exception) as exc:
            app.test_client.get(
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
        _, response = app.test_client.get(
            f"https://127.0.0.1:{port}/sni",
            server_kwargs={"ssl": ssl_list},
        )
        assert response.status == 200
        assert response.text == "foo.sanic.test"

    with replace_server_name("sanic.test"):
        with pytest.raises(Exception) as exc:
            _, response = app.test_client.get(
                f"https://127.0.0.1:{port}/sni",
                server_kwargs={"ssl": ssl_list},
            )
        assert "Request and response object expected" in str(exc.value)
    with replace_server_name("sub.foo.sanic.test"):
        with pytest.raises(Exception) as exc:
            _, response = app.test_client.get(
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
        app.test_client.get("/test", server_kwargs={"ssl": ssl_dict})

    assert str(excinfo.value) == "SSL dict needs filenames for cert and key."


def test_invalid_ssl_type(app):
    @app.get("/test")
    async def handler(request):
        return text("ssl test")

    with pytest.raises(ValueError) as excinfo:
        app.test_client.get("/test", server_kwargs={"ssl": False})

    assert "Invalid ssl argument" in str(excinfo.value)


def test_cert_file_on_pathlist(app):
    @app.get("/test")
    async def handler(request):
        return text("ssl test")

    ssl_list = [sanic_cert]

    with pytest.raises(ValueError) as excinfo:
        app.test_client.get("/test", server_kwargs={"ssl": ssl_list})

    assert "folder expected" in str(excinfo.value)
    assert sanic_cert in str(excinfo.value)


def test_missing_cert_path(app):
    @app.get("/test")
    async def handler(request):
        return text("ssl test")

    ssl_list = [invalid_dir]

    with pytest.raises(ValueError) as excinfo:
        app.test_client.get("/test", server_kwargs={"ssl": ssl_list})

    assert "not found" in str(excinfo.value)
    assert invalid_dir + "/privkey.pem" in str(excinfo.value)


def test_missing_cert_file(app):
    @app.get("/test")
    async def handler(request):
        return text("ssl test")

    invalid2 = invalid_dir.replace("nonexist", "certmissing")
    ssl_list = [invalid2]

    with pytest.raises(ValueError) as excinfo:
        app.test_client.get("/test", server_kwargs={"ssl": ssl_list})

    assert "not found" in str(excinfo.value)
    assert invalid2 + "/fullchain.pem" in str(excinfo.value)


def test_no_certs_on_list(app):
    @app.get("/test")
    async def handler(request):
        return text("ssl test")

    ssl_list = [None]

    with pytest.raises(ValueError) as excinfo:
        app.test_client.get("/test", server_kwargs={"ssl": ssl_list})

    assert "No certificates" in str(excinfo.value)


def test_logger_vhosts(caplog):
    app = Sanic(name="test_logger_vhosts")

    @app.after_server_start
    def stop(*args):
        app.stop()

    with caplog.at_level(logging.INFO):
        app.run(host="127.0.0.1", port=42102, ssl=[localhost_dir, sanic_dir])

    logmsg = [
        m for s, l, m in caplog.record_tuples if m.startswith("Certificate")
    ][0]

    assert logmsg == (
        "Certificate vhosts: localhost, 127.0.0.1, 0:0:0:0:0:0:0:1, "
        "sanic.example, www.sanic.example, *.sanic.test, "
        "2001:DB8:0:0:0:0:0:541C"
    )


def test_mk_cert_creator_default(app: Sanic):
    cert_creator = MkcertCreator(app, _default, _default)
    assert isinstance(cert_creator.tmpdir, Path)
    assert cert_creator.tmpdir.exists()


def test_mk_cert_creator_is_supported(app):
    cert_creator = MkcertCreator(app, _default, _default)
    with patch("subprocess.run") as run:
        cert_creator.check_supported()
        run.assert_called_once_with(
            ["mkcert", "-help"],
            check=True,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )


def test_mk_cert_creator_is_not_supported(app):
    cert_creator = MkcertCreator(app, _default, _default)
    with patch("subprocess.run") as run:
        run.side_effect = Exception("")
        with pytest.raises(
            SanicException, match="Sanic is attempting to use mkcert"
        ):
            cert_creator.check_supported()


def test_mk_cert_creator_generate_cert_default(app):
    cert_creator = MkcertCreator(app, _default, _default)
    with patch("subprocess.run") as run:
        with patch("sanic.http.tls.creators.CertSimple"):
            retval = Mock()
            retval.stdout = "foo"
            run.return_value = retval
            cert_creator.generate_cert("localhost")
            run.assert_called_once()


def test_mk_cert_creator_generate_cert_localhost(app):
    cert_creator = MkcertCreator(app, localhost_key, localhost_cert)
    with patch("subprocess.run") as run:
        with patch("sanic.http.tls.creators.CertSimple"):
            cert_creator.generate_cert("localhost")
            run.assert_not_called()


def test_trustme_creator_default(app: Sanic):
    cert_creator = TrustmeCreator(app, _default, _default)
    assert isinstance(cert_creator.tmpdir, Path)
    assert cert_creator.tmpdir.exists()


def test_trustme_creator_is_supported(app, monkeypatch):
    monkeypatch.setattr(sanic.http.tls.creators, "TRUSTME_INSTALLED", True)
    cert_creator = TrustmeCreator(app, _default, _default)
    cert_creator.check_supported()


def test_trustme_creator_is_not_supported(app, monkeypatch):
    monkeypatch.setattr(sanic.http.tls.creators, "TRUSTME_INSTALLED", False)
    cert_creator = TrustmeCreator(app, _default, _default)
    with pytest.raises(
        SanicException, match="Sanic is attempting to use trustme"
    ):
        cert_creator.check_supported()


def test_trustme_creator_generate_cert_default(
    app, monkeypatch, trustme, issue_cert, server_cert, ca
):
    monkeypatch.setattr(sanic.http.tls.creators, "trustme", trustme)
    cert_creator = TrustmeCreator(app, _default, _default)
    cert = cert_creator.generate_cert("localhost")

    assert isinstance(cert, SanicSSLContext)
    trustme.CA.assert_called_once_with()
    issue_cert.assert_called_once_with("localhost")
    server_cert.configure_cert.assert_called_once()
    ca.configure_trust.assert_called_once()
    ca.cert_pem.write_to_path.assert_called_once_with(str(cert.sanic["cert"]))
    write_to_path = server_cert.private_key_and_cert_chain_pem.write_to_path
    write_to_path.assert_called_once_with(str(cert.sanic["key"]))


def test_trustme_creator_generate_cert_localhost(
    app, monkeypatch, trustme, server_cert, ca
):
    monkeypatch.setattr(sanic.http.tls.creators, "trustme", trustme)
    cert_creator = TrustmeCreator(app, localhost_key, localhost_cert)
    cert_creator.generate_cert("localhost")

    ca.cert_pem.write_to_path.assert_called_once_with(localhost_cert)
    write_to_path = server_cert.private_key_and_cert_chain_pem.write_to_path
    write_to_path.assert_called_once_with(localhost_key)


def test_get_ssl_context_with_ssl_context(app):
    mock_context = Mock()
    context = get_ssl_context(app, mock_context)
    assert context is mock_context


def test_get_ssl_context_in_production(app):
    app.state.mode = Mode.PRODUCTION
    with pytest.raises(
        SanicException,
        match="Cannot run Sanic as an HTTPS server in PRODUCTION mode",
    ):
        get_ssl_context(app, None)


@pytest.mark.parametrize(
    "requirement,mk_supported,trustme_supported,mk_called,trustme_called,err",
    (
        (LocalCertCreator.AUTO, True, False, True, False, None),
        (LocalCertCreator.AUTO, True, True, True, False, None),
        (LocalCertCreator.AUTO, False, True, False, True, None),
        (
            LocalCertCreator.AUTO,
            False,
            False,
            False,
            False,
            "Sanic could not find package to create a TLS certificate",
        ),
        (LocalCertCreator.MKCERT, True, False, True, False, None),
        (LocalCertCreator.MKCERT, True, True, True, False, None),
        (LocalCertCreator.MKCERT, False, True, False, False, "Nope"),
        (LocalCertCreator.MKCERT, False, False, False, False, "Nope"),
        (LocalCertCreator.TRUSTME, True, False, False, False, "Nope"),
        (LocalCertCreator.TRUSTME, True, True, False, True, None),
        (LocalCertCreator.TRUSTME, False, True, False, True, None),
        (LocalCertCreator.TRUSTME, False, False, False, False, "Nope"),
    ),
)
def test_get_ssl_context_only_mkcert(
    app,
    monkeypatch,
    MockMkcertCreator,
    MockTrustmeCreator,
    requirement,
    mk_supported,
    trustme_supported,
    mk_called,
    trustme_called,
    err,
):
    app.state.mode = Mode.DEBUG
    app.config.LOCAL_CERT_CREATOR = requirement
    monkeypatch.setattr(
        sanic.http.tls.creators, "MkcertCreator", MockMkcertCreator
    )
    monkeypatch.setattr(
        sanic.http.tls.creators, "TrustmeCreator", MockTrustmeCreator
    )
    MockMkcertCreator.SUPPORTED = mk_supported
    MockTrustmeCreator.SUPPORTED = trustme_supported

    if err:
        with pytest.raises(SanicException, match=err):
            get_ssl_context(app, None)
    else:
        get_ssl_context(app, None)

    if mk_called:
        MockMkcertCreator.generate_cert.assert_called_once_with("localhost")
    else:
        MockMkcertCreator.generate_cert.assert_not_called()
    if trustme_called:
        MockTrustmeCreator.generate_cert.assert_called_once_with("localhost")
    else:
        MockTrustmeCreator.generate_cert.assert_not_called()


# def test_no_http3_with_trustme(
#     app,
#     monkeypatch,
#     MockTrustmeCreator,
# ):
#     monkeypatch.setattr(
#         sanic.http.tls.creators, "TrustmeCreator", MockTrustmeCreator
#     )
#     MockTrustmeCreator.SUPPORTED = True
#     app.config.LOCAL_CERT_CREATOR = "TRUSTME"
#     with pytest.raises(
#         SanicException,
#         match=(
#             "Sorry, you cannot currently use trustme as a local certificate "
#             "generator for an HTTP/3 server"
#         ),
#     ):
#         app.run(version=3, debug=True)


def test_sanic_ssl_context_create():
    context = ssl.SSLContext()
    sanic_context = SanicSSLContext.create_from_ssl_context(context)

    assert sanic_context is context
    assert isinstance(sanic_context, SanicSSLContext)


def test_ssl_in_multiprocess_mode(app: Sanic, caplog):

    ssl_dict = {"cert": localhost_cert, "key": localhost_key}
    event = Event()

    @app.main_process_start
    async def main_start(app: Sanic):
        app.shared_ctx.event = event

    @app.after_server_start
    async def shutdown(app):
        app.shared_ctx.event.set()
        app.stop()

    assert not event.is_set()
    with caplog.at_level(logging.INFO):
        app.run(ssl=ssl_dict)
    assert event.is_set()

    assert (
        "sanic.root",
        logging.INFO,
        "Goin' Fast @ https://127.0.0.1:8000",
    ) in caplog.record_tuples
