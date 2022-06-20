import base64
import logging

from json import dumps as json_dumps
from json import loads as json_loads
from urllib.parse import urlparse

import pytest

from sanic_testing.testing import (
    ASGI_BASE_URL,
    ASGI_PORT,
    HOST,
    PORT,
    SanicTestClient,
)

from sanic import Blueprint, Sanic
from sanic.exceptions import ServerError
from sanic.request import DEFAULT_HTTP_CONTENT_TYPE, RequestParameters
from sanic.response import html, json, text


def encode_basic_auth_credentials(username, password):
    return base64.b64encode(f"{username}:{password}".encode()).decode("ascii")


# ------------------------------------------------------------ #
#  GET
# ------------------------------------------------------------ #


def test_sync(app):
    @app.route("/")
    def handler(request):
        return text("Hello")

    request, response = app.test_client.get("/")

    assert response.body == b"Hello"


@pytest.mark.asyncio
async def test_sync_asgi(app):
    @app.route("/")
    def handler(request):
        return text("Hello")

    request, response = await app.asgi_client.get("/")

    assert response.body == b"Hello"


def test_ip(app):
    @app.route("/")
    def handler(request):
        return text(f"{request.ip}")

    request, response = app.test_client.get("/")

    assert response.body == b"127.0.0.1"


@pytest.mark.asyncio
async def test_url_asgi(app):
    @app.route("/")
    def handler(request):
        return text(f"{request.url}")

    request, response = await app.asgi_client.get("/")

    if response.body.decode().endswith("/") and not ASGI_BASE_URL.endswith(
        "/"
    ):
        response.body[:-1] == ASGI_BASE_URL.encode()
    else:
        assert response.body == ASGI_BASE_URL.encode()


def test_text(app):
    @app.route("/")
    async def handler(request):
        return text("Hello")

    request, response = app.test_client.get("/")

    assert response.body == b"Hello"


def test_html(app):
    class Foo:
        def __html__(self):
            return "<h1>Foo</h1>"

        def _repr_html_(self):
            return "<h1>Foo object repr</h1>"

    class Bar:
        def _repr_html_(self):
            return "<h1>Bar object repr</h1>"

    @app.route("/")
    async def handler(request):
        return html("<h1>Hello</h1>")

    @app.route("/foo")
    async def handler(request):
        return html(Foo())

    @app.route("/bar")
    async def handler(request):
        return html(Bar())

    request, response = app.test_client.get("/")
    assert response.content_type == "text/html; charset=utf-8"
    assert response.body == b"<h1>Hello</h1>"

    request, response = app.test_client.get("/foo")
    assert response.body == b"<h1>Foo</h1>"

    request, response = app.test_client.get("/bar")
    assert response.body == b"<h1>Bar object repr</h1>"


@pytest.mark.asyncio
async def test_text_asgi(app):
    @app.route("/")
    async def handler(request):
        return text("Hello")

    request, response = await app.asgi_client.get("/")

    assert response.body == b"Hello"


def test_headers(app):
    @app.route("/")
    async def handler(request):
        headers = {"spam": "great"}
        return text("Hello", headers=headers)

    request, response = app.test_client.get("/")

    assert response.headers.get("spam") == "great"


@pytest.mark.asyncio
async def test_headers_asgi(app):
    @app.route("/")
    async def handler(request):
        headers = {"spam": "great"}
        return text("Hello", headers=headers)

    request, response = await app.asgi_client.get("/")

    assert response.headers.get("spam") == "great"


def test_non_str_headers(app):
    @app.route("/")
    async def handler(request):
        headers = {"answer": 42}
        return text("Hello", headers=headers)

    request, response = app.test_client.get("/")

    assert response.headers.get("answer") == "42"


@pytest.mark.asyncio
async def test_non_str_headers_asgi(app):
    @app.route("/")
    async def handler(request):
        headers = {"answer": 42}
        return text("Hello", headers=headers)

    request, response = await app.asgi_client.get("/")

    assert response.headers.get("answer") == "42"


def test_invalid_response(app):
    @app.exception(ServerError)
    def handler_exception(request, exception):
        return text("Internal Server Error.", 500)

    @app.route("/")
    async def handler(request):
        return "This should fail"

    request, response = app.test_client.get("/")
    assert response.status == 500
    assert response.body == b"Internal Server Error."


@pytest.mark.asyncio
async def test_invalid_response_asgi(app):
    @app.exception(ServerError)
    def handler_exception(request, exception):
        return text("Internal Server Error.", 500)

    @app.route("/")
    async def handler(request):
        return "This should fail"

    request, response = await app.asgi_client.get("/")
    assert response.status == 500
    assert response.body == b"Internal Server Error."


def test_json(app):
    @app.route("/")
    async def handler(request):
        return json({"test": True})

    request, response = app.test_client.get("/")

    results = json_loads(response.text)

    assert results.get("test") is True


@pytest.mark.asyncio
async def test_json_asgi(app):
    @app.route("/")
    async def handler(request):
        return json({"test": True})

    request, response = await app.asgi_client.get("/")

    results = json_loads(response.body)

    assert results.get("test") is True


def test_empty_json(app):
    @app.route("/")
    async def handler(request):
        assert request.json is None
        return json(request.json)

    request, response = app.test_client.get("/")
    assert response.status == 200
    assert response.body == b"null"


@pytest.mark.asyncio
async def test_empty_json_asgi(app):
    @app.route("/")
    async def handler(request):
        assert request.json is None
        return json(request.json)

    request, response = await app.asgi_client.get("/")
    assert response.status == 200
    assert response.body == b"null"


def test_echo_json(app):
    @app.post("/")
    async def handler(request):
        return json(request.json)

    data = {"foo": "bar"}
    request, response = app.test_client.post("/", json=data)

    assert response.status == 200
    assert response.json == data


@pytest.mark.asyncio
async def test_echo_json_asgi(app):
    @app.post("/")
    async def handler(request):
        return json(request.json)

    data = {"foo": "bar"}
    request, response = await app.asgi_client.post("/", json=data)

    assert response.status == 200
    assert response.json == data


def test_invalid_json(app):
    @app.post("/")
    async def handler(request):
        return json(request.json)

    data = "I am not json"
    request, response = app.test_client.post("/", data=data)

    assert response.status == 400


@pytest.mark.asyncio
async def test_invalid_json_asgi(app):
    @app.post("/")
    async def handler(request):
        return json(request.json)

    data = "I am not json"
    request, response = await app.asgi_client.post("/", data=data)

    assert response.status == 400


def test_query_string(app):
    @app.route("/")
    async def handler(request):
        return text("OK")

    request, response = app.test_client.get(
        "/", params=[("test1", "1"), ("test2", "false"), ("test2", "true")]
    )

    assert request.args.get("test1") == "1"
    assert request.args.get("test2") == "false"
    assert request.args.getlist("test2") == ["false", "true"]
    assert request.args.getlist("test1") == ["1"]
    assert request.args.get("test3", default="My value") == "My value"


def test_popped_stays_popped(app):
    @app.route("/")
    async def handler(request):
        return text("OK")

    request, response = app.test_client.get("/", params=[("test1", "1")])

    assert request.args.pop("test1") == ["1"]
    assert "test1" not in request.args


@pytest.mark.asyncio
async def test_query_string_asgi(app):
    @app.route("/")
    async def handler(request):
        return text("OK")

    request, response = await app.asgi_client.get(
        "/", params=[("test1", "1"), ("test2", "false"), ("test2", "true")]
    )

    assert request.args.get("test1") == "1"
    assert request.args.get("test2") == "false"
    assert request.args.getlist("test2") == ["false", "true"]
    assert request.args.getlist("test1") == ["1"]
    assert request.args.get("test3", default="My value") == "My value"


def test_uri_template(app):
    @app.route("/foo/<id:int>/bar/<name:[A-z]+>")
    async def handler(request, id, name):
        return text("OK")

    request, response = app.test_client.get("/foo/123/bar/baz")
    assert request.uri_template == "/foo/<id:int>/bar/<name:[A-z]+>"


@pytest.mark.asyncio
async def test_uri_template_asgi(app):
    @app.route("/foo/<id:int>/bar/<name:[A-z]+>")
    async def handler(request, id, name):
        return text("OK")

    request, response = await app.asgi_client.get("/foo/123/bar/baz")
    assert request.uri_template == "/foo/<id:int>/bar/<name:[A-z]+>"


@pytest.mark.parametrize(
    ("auth_type", "token"),
    [
        # uuid4 generated token set in "Authorization" header
        (None, "a1d895e0-553a-421a-8e22-5ff8ecb48cbf"),
        # uuid4 generated token with API Token authorization
        ("Token", "a1d895e0-553a-421a-8e22-5ff8ecb48cbf"),
        # uuid4 generated token with Bearer Token authorization
        ("Bearer", "a1d895e0-553a-421a-8e22-5ff8ecb48cbf"),
        # no Authorization header
        (None, None),
    ],
)
def test_token(app, auth_type, token):
    @app.route("/")
    async def handler(request):
        return text("OK")

    if token:
        headers = {
            "content-type": "application/json",
            "Authorization": f"{auth_type} {token}"
            if auth_type
            else f"{token}",
        }
    else:
        headers = {"content-type": "application/json"}

    request, response = app.test_client.get("/", headers=headers)
    assert request.token == token


@pytest.mark.parametrize(
    ("auth_type", "token", "username", "password"),
    [
        # uuid4 generated token set in "Authorization" header
        (None, "a1d895e0-553a-421a-8e22-5ff8ecb48cbf", None, None),
        # uuid4 generated token with API Token authorization
        ("Token", "a1d895e0-553a-421a-8e22-5ff8ecb48cbf", None, None),
        # uuid4 generated token with Bearer Token authorization
        ("Bearer", "a1d895e0-553a-421a-8e22-5ff8ecb48cbf", None, None),
        # username and password with Basic Auth authorization
        (
            "Basic",
            encode_basic_auth_credentials("some_username", "some_pass"),
            "some_username",
            "some_pass",
        ),
        # no Authorization header
        (None, None, None, None),
    ],
)
def test_credentials(app, capfd, auth_type, token, username, password):
    @app.route("/")
    async def handler(request):
        return text("OK")

    if token:
        headers = {
            "content-type": "application/json",
            "Authorization": f"{auth_type} {token}"
            if auth_type
            else f"{token}",
        }
    else:
        headers = {"content-type": "application/json"}

    request, response = app.test_client.get("/", headers=headers)

    if auth_type == "Basic":
        assert request.credentials.username == username
        assert request.credentials.password == password
    else:
        _, err = capfd.readouterr()
        with pytest.raises(AttributeError):
            request.credentials.password
            assert "Password is available for Basic Auth only" in err
            request.credentials.username
            assert "Username is available for Basic Auth only" in err

    if token:
        assert request.credentials.token == token
        assert request.credentials.auth_type == auth_type
    else:
        assert request.credentials is None
        assert not hasattr(request.credentials, "token")
        assert not hasattr(request.credentials, "auth_type")
        assert not hasattr(request.credentials, "_username")
        assert not hasattr(request.credentials, "_password")


def test_content_type(app):
    @app.route("/")
    async def handler(request):
        return text(request.content_type)

    request, response = app.test_client.get("/")
    assert request.content_type == DEFAULT_HTTP_CONTENT_TYPE
    assert response.body.decode() == DEFAULT_HTTP_CONTENT_TYPE

    headers = {"content-type": "application/json"}
    request, response = app.test_client.get("/", headers=headers)
    assert request.content_type == "application/json"
    assert response.body == b"application/json"


@pytest.mark.asyncio
async def test_content_type_asgi(app):
    @app.route("/")
    async def handler(request):
        return text(request.content_type)

    request, response = await app.asgi_client.get("/")
    assert request.content_type == DEFAULT_HTTP_CONTENT_TYPE
    assert response.body.decode() == DEFAULT_HTTP_CONTENT_TYPE

    headers = {"content-type": "application/json"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.content_type == "application/json"
    assert response.body == b"application/json"


def test_standard_forwarded(app):
    @app.route("/")
    async def handler(request):
        return json(request.forwarded)

    # Without configured FORWARDED_SECRET, x-headers should be respected
    app.config.PROXIES_COUNT = 1
    app.config.REAL_IP_HEADER = "x-real-ip"
    headers = {
        "Forwarded": (
            'for=1.1.1.1, for=injected;host="'
            ', for="[::2]";proto=https;host=me.tld;path="/app/";secret=mySecret'
            ",for=broken;;secret=b0rked"
            ", for=127.0.0.3;scheme=http;port=1234"
        ),
        "X-Real-IP": "127.0.0.2",
        "X-Forwarded-For": "127.0.1.1",
        "X-Scheme": "ws",
        "Host": "local.site",
    }
    request, response = app.test_client.get("/", headers=headers)
    assert response.json == {"for": "127.0.0.2", "proto": "ws"}
    assert request.remote_addr == "127.0.0.2"
    assert request.scheme == "ws"
    assert request.server_name == "local.site"
    assert request.server_port == 80

    app.config.FORWARDED_SECRET = "mySecret"
    request, response = app.test_client.get("/", headers=headers)
    assert response.json == {
        "for": "[::2]",
        "proto": "https",
        "host": "me.tld",
        "path": "/app/",
        "secret": "mySecret",
    }
    assert request.remote_addr == "[::2]"
    assert request.server_name == "me.tld"
    assert request.scheme == "https"
    assert request.server_port == 443

    # Empty Forwarded header -> use X-headers
    headers["Forwarded"] = ""
    request, response = app.test_client.get("/", headers=headers)
    assert response.json == {"for": "127.0.0.2", "proto": "ws"}

    # Header present but not matching anything
    request, response = app.test_client.get("/", headers={"Forwarded": "."})
    assert response.json == {}

    # Forwarded header present but no matching secret -> use X-headers
    headers = {
        "Forwarded": "for=1.1.1.1;secret=x, for=127.0.0.1",
        "X-Real-IP": "127.0.0.2",
    }
    request, response = app.test_client.get("/", headers=headers)
    assert response.json == {"for": "127.0.0.2"}
    assert request.remote_addr == "127.0.0.2"

    # Different formatting and hitting both ends of the header
    headers = {"Forwarded": 'Secret="mySecret";For=127.0.0.4;Port=1234'}
    request, response = app.test_client.get("/", headers=headers)
    assert response.json == {
        "for": "127.0.0.4",
        "port": 1234,
        "secret": "mySecret",
    }

    # Test escapes (modify this if you see anyone implementing quoted-pairs)
    headers = {"Forwarded": 'for=test;quoted="\\,x=x;y=\\";secret=mySecret'}
    request, response = app.test_client.get("/", headers=headers)
    assert response.json == {
        "for": "test",
        "quoted": "\\,x=x;y=\\",
        "secret": "mySecret",
    }

    # Secret insulated by malformed field #1
    headers = {"Forwarded": "for=test;secret=mySecret;b0rked;proto=wss;"}
    request, response = app.test_client.get("/", headers=headers)
    assert response.json == {"for": "test", "secret": "mySecret"}

    # Secret insulated by malformed field #2
    headers = {"Forwarded": "for=test;b0rked;secret=mySecret;proto=wss"}
    request, response = app.test_client.get("/", headers=headers)
    assert response.json == {"proto": "wss", "secret": "mySecret"}

    # Unexpected termination should not lose existing acceptable values
    headers = {"Forwarded": "b0rked;secret=mySecret;proto=wss"}
    request, response = app.test_client.get("/", headers=headers)
    assert response.json == {"proto": "wss", "secret": "mySecret"}

    # Field normalization
    headers = {
        "Forwarded": 'PROTO=WSS;BY="CAFE::8000";FOR=unknown;PORT=X;HOST="A:2";'
        'PATH="/With%20Spaces%22Quoted%22/sanicApp?key=val";SECRET=mySecret'
    }
    request, response = app.test_client.get("/", headers=headers)
    assert response.json == {
        "proto": "wss",
        "by": "[cafe::8000]",
        "host": "a:2",
        "path": '/With Spaces"Quoted"/sanicApp?key=val',
        "secret": "mySecret",
    }

    # Using "by" field as secret
    app.config.FORWARDED_SECRET = "_proxySecret"
    headers = {"Forwarded": "for=1.2.3.4; by=_proxySecret"}
    request, response = app.test_client.get("/", headers=headers)
    assert response.json == {"for": "1.2.3.4", "by": "_proxySecret"}


@pytest.mark.asyncio
async def test_standard_forwarded_asgi(app):
    @app.route("/")
    async def handler(request):
        return json(request.forwarded)

    # Without configured FORWARDED_SECRET, x-headers should be respected
    app.config.PROXIES_COUNT = 1
    app.config.REAL_IP_HEADER = "x-real-ip"
    headers = {
        "Forwarded": (
            'for=1.1.1.1, for=injected;host="'
            ', for="[::2]";proto=https;host=me.tld;path="/app/";secret=mySecret'
            ",for=broken;;secret=b0rked"
            ", for=127.0.0.3;scheme=http;port=1234"
        ),
        "X-Real-IP": "127.0.0.2",
        "X-Forwarded-For": "127.0.1.1",
        "X-Scheme": "ws",
    }
    request, response = await app.asgi_client.get("/", headers=headers)

    assert response.json == {"for": "127.0.0.2", "proto": "ws"}
    assert request.remote_addr == "127.0.0.2"
    assert request.scheme == "ws"
    assert request.server_port == ASGI_PORT

    app.config.FORWARDED_SECRET = "mySecret"
    request, response = await app.asgi_client.get("/", headers=headers)
    assert response.json == {
        "for": "[::2]",
        "proto": "https",
        "host": "me.tld",
        "path": "/app/",
        "secret": "mySecret",
    }
    assert request.remote_addr == "[::2]"
    assert request.server_name == "me.tld"
    assert request.scheme == "https"
    assert request.server_port == 443

    # Empty Forwarded header -> use X-headers
    headers["Forwarded"] = ""
    request, response = await app.asgi_client.get("/", headers=headers)
    assert response.json == {"for": "127.0.0.2", "proto": "ws"}

    # Header present but not matching anything
    request, response = await app.asgi_client.get(
        "/", headers={"Forwarded": "."}
    )
    assert response.json == {}

    # Forwarded header present but no matching secret -> use X-headers
    headers = {
        "Forwarded": "for=1.1.1.1;secret=x, for=127.0.0.1",
        "X-Real-IP": "127.0.0.2",
    }
    request, response = await app.asgi_client.get("/", headers=headers)
    assert response.json == {"for": "127.0.0.2"}
    assert request.remote_addr == "127.0.0.2"

    # Different formatting and hitting both ends of the header
    headers = {"Forwarded": 'Secret="mySecret";For=127.0.0.4;Port=1234'}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert response.json == {
        "for": "127.0.0.4",
        "port": 1234,
        "secret": "mySecret",
    }

    # Test escapes (modify this if you see anyone implementing quoted-pairs)
    headers = {"Forwarded": 'for=test;quoted="\\,x=x;y=\\";secret=mySecret'}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert response.json == {
        "for": "test",
        "quoted": "\\,x=x;y=\\",
        "secret": "mySecret",
    }

    # Secret insulated by malformed field #1
    headers = {"Forwarded": "for=test;secret=mySecret;b0rked;proto=wss;"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert response.json == {"for": "test", "secret": "mySecret"}

    # Secret insulated by malformed field #2
    headers = {"Forwarded": "for=test;b0rked;secret=mySecret;proto=wss"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert response.json == {"proto": "wss", "secret": "mySecret"}

    # Unexpected termination should not lose existing acceptable values
    headers = {"Forwarded": "b0rked;secret=mySecret;proto=wss"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert response.json == {"proto": "wss", "secret": "mySecret"}

    # Field normalization
    headers = {
        "Forwarded": 'PROTO=WSS;BY="CAFE::8000";FOR=unknown;PORT=X;HOST="A:2";'
        'PATH="/With%20Spaces%22Quoted%22/sanicApp?key=val";SECRET=mySecret'
    }
    request, response = await app.asgi_client.get("/", headers=headers)
    assert response.json == {
        "proto": "wss",
        "by": "[cafe::8000]",
        "host": "a:2",
        "path": '/With Spaces"Quoted"/sanicApp?key=val',
        "secret": "mySecret",
    }

    # Using "by" field as secret
    app.config.FORWARDED_SECRET = "_proxySecret"
    headers = {"Forwarded": "for=1.2.3.4; by=_proxySecret"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert response.json == {
        "for": "1.2.3.4",
        "by": "_proxySecret",
    }


def test_remote_addr_with_two_proxies(app):
    app.config.PROXIES_COUNT = 2
    app.config.REAL_IP_HEADER = "x-real-ip"

    @app.route("/")
    async def handler(request):
        return text(request.remote_addr)

    headers = {"X-Real-IP": "127.0.0.2", "X-Forwarded-For": "127.0.1.1"}
    request, response = app.test_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.0.2"
    assert response.body == b"127.0.0.2"

    headers = {"X-Forwarded-For": "127.0.1.1"}
    request, response = app.test_client.get("/", headers=headers)
    assert request.remote_addr == ""
    assert response.body == b""

    headers = {"X-Forwarded-For": "127.0.0.1, 127.0.1.2"}
    request, response = app.test_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.0.1"
    assert response.body == b"127.0.0.1"

    request, response = app.test_client.get("/")
    assert request.remote_addr == ""
    assert response.body == b""

    headers = {"X-Forwarded-For": "127.0.0.1, ,   ,,127.0.1.2"}
    request, response = app.test_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.0.1"
    assert response.body == b"127.0.0.1"

    headers = {
        "X-Forwarded-For": ", 127.0.2.2, ,  ,127.0.0.1, ,   ,,127.0.1.2"
    }
    request, response = app.test_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.0.1"
    assert response.body == b"127.0.0.1"


@pytest.mark.asyncio
async def test_remote_addr_with_two_proxies_asgi(app):
    app.config.PROXIES_COUNT = 2
    app.config.REAL_IP_HEADER = "x-real-ip"

    @app.route("/")
    async def handler(request):
        return text(request.remote_addr)

    headers = {"X-Real-IP": "127.0.0.2", "X-Forwarded-For": "127.0.1.1"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.0.2"
    assert response.body == b"127.0.0.2"

    headers = {"X-Forwarded-For": "127.0.1.1"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.remote_addr == ""
    assert response.body == b""

    headers = {"X-Forwarded-For": "127.0.0.1, 127.0.1.2"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.0.1"
    assert response.body == b"127.0.0.1"

    request, response = await app.asgi_client.get("/")
    assert request.remote_addr == ""
    assert response.body == b""

    headers = {"X-Forwarded-For": "127.0.0.1, ,   ,,127.0.1.2"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.0.1"
    assert response.body == b"127.0.0.1"

    headers = {
        "X-Forwarded-For": ", 127.0.2.2, ,  ,127.0.0.1, ,   ,,127.0.1.2"
    }
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.0.1"
    assert response.body == b"127.0.0.1"


def test_remote_addr_without_proxy(app):
    app.config.PROXIES_COUNT = 0

    @app.route("/")
    async def handler(request):
        return text(request.remote_addr)

    headers = {"X-Real-IP": "127.0.0.2", "X-Forwarded-For": "127.0.1.1"}
    request, response = app.test_client.get("/", headers=headers)
    assert request.remote_addr == ""
    assert response.body == b""

    headers = {"X-Forwarded-For": "127.0.1.1"}
    request, response = app.test_client.get("/", headers=headers)
    assert request.remote_addr == ""
    assert response.body == b""

    headers = {"X-Forwarded-For": "127.0.0.1, 127.0.1.2"}
    request, response = app.test_client.get("/", headers=headers)
    assert request.remote_addr == ""
    assert response.body == b""


@pytest.mark.asyncio
async def test_remote_addr_without_proxy_asgi(app):
    app.config.PROXIES_COUNT = 0

    @app.route("/")
    async def handler(request):
        return text(request.remote_addr)

    headers = {"X-Real-IP": "127.0.0.2", "X-Forwarded-For": "127.0.1.1"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.remote_addr == ""
    assert response.body == b""

    headers = {"X-Forwarded-For": "127.0.1.1"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.remote_addr == ""
    assert response.body == b""

    headers = {"X-Forwarded-For": "127.0.0.1, 127.0.1.2"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.remote_addr == ""
    assert response.body == b""


def test_remote_addr_custom_headers(app):
    app.config.PROXIES_COUNT = 1
    app.config.REAL_IP_HEADER = "Client-IP"
    app.config.FORWARDED_FOR_HEADER = "Forwarded"

    @app.route("/")
    async def handler(request):
        return text(request.remote_addr)

    headers = {"X-Real-IP": "127.0.0.2", "Forwarded": "127.0.1.1"}
    request, response = app.test_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.1.1"
    assert response.body == b"127.0.1.1"

    headers = {"X-Forwarded-For": "127.0.1.1"}
    request, response = app.test_client.get("/", headers=headers)
    assert request.remote_addr == ""
    assert response.body == b""

    headers = {"Client-IP": "127.0.0.2", "Forwarded": "127.0.1.1"}
    request, response = app.test_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.0.2"
    assert response.body == b"127.0.0.2"


@pytest.mark.asyncio
async def test_remote_addr_custom_headers_asgi(app):
    app.config.PROXIES_COUNT = 1
    app.config.REAL_IP_HEADER = "Client-IP"
    app.config.FORWARDED_FOR_HEADER = "Forwarded"

    @app.route("/")
    async def handler(request):
        return text(request.remote_addr)

    headers = {"X-Real-IP": "127.0.0.2", "Forwarded": "127.0.1.1"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.1.1"
    assert response.body == b"127.0.1.1"

    headers = {"X-Forwarded-For": "127.0.1.1"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.remote_addr == ""
    assert response.body == b""

    headers = {"Client-IP": "127.0.0.2", "Forwarded": "127.0.1.1"}
    request, response = await app.asgi_client.get("/", headers=headers)
    assert request.remote_addr == "127.0.0.2"
    assert response.body == b"127.0.0.2"


def test_forwarded_scheme(app):
    @app.route("/")
    async def handler(request):
        return text(request.remote_addr)

    app.config.PROXIES_COUNT = 1
    request, response = app.test_client.get("/")
    assert request.scheme == "http"

    request, response = app.test_client.get(
        "/",
        headers={"X-Forwarded-For": "127.1.2.3", "X-Forwarded-Proto": "https"},
    )
    assert request.scheme == "https"

    request, response = app.test_client.get(
        "/", headers={"X-Forwarded-For": "127.1.2.3", "X-Scheme": "https"}
    )
    assert request.scheme == "https"


def test_match_info(app):
    @app.route("/api/v1/user/<user_id>/")
    async def handler(request, user_id):
        return json(request.match_info)

    request, response = app.test_client.get("/api/v1/user/sanic_user/")

    assert request.match_info == {"user_id": "sanic_user"}
    assert json_loads(response.text) == {"user_id": "sanic_user"}


@pytest.mark.asyncio
async def test_match_info_asgi(app):
    @app.route("/api/v1/user/<user_id>/")
    async def handler(request, user_id):
        return json(request.match_info)

    request, response = await app.asgi_client.get("/api/v1/user/sanic_user/")

    assert request.match_info == {"user_id": "sanic_user"}
    assert json_loads(response.body) == {"user_id": "sanic_user"}


# ------------------------------------------------------------ #
#  POST
# ------------------------------------------------------------ #


def test_post_json(app):
    @app.route("/", methods=["POST"])
    async def handler(request):
        return text("OK")

    payload = {"test": "OK"}
    headers = {"content-type": "application/json"}

    request, response = app.test_client.post(
        "/", data=json_dumps(payload), headers=headers
    )

    assert request.json.get("test") == "OK"
    assert request.json.get("test") == "OK"  # for request.parsed_json
    assert response.body == b"OK"


@pytest.mark.asyncio
async def test_post_json_asgi(app):
    @app.route("/", methods=["POST"])
    async def handler(request):
        return text("OK")

    payload = {"test": "OK"}
    headers = {"content-type": "application/json"}

    request, response = await app.asgi_client.post(
        "/", data=json_dumps(payload), headers=headers
    )

    assert request.json.get("test") == "OK"
    assert request.json.get("test") == "OK"  # for request.parsed_json
    assert response.body == b"OK"


def test_post_form_urlencoded(app):
    @app.route("/", methods=["POST"])
    async def handler(request):
        return text("OK")

    payload = "test=OK"
    headers = {"content-type": "application/x-www-form-urlencoded"}

    request, response = app.test_client.post(
        "/", data=payload, headers=headers
    )

    assert request.form.get("test") == "OK"
    assert request.form.get("test") == "OK"  # For request.parsed_form


@pytest.mark.asyncio
async def test_post_form_urlencoded_asgi(app):
    @app.route("/", methods=["POST"])
    async def handler(request):
        return text("OK")

    payload = "test=OK"
    headers = {"content-type": "application/x-www-form-urlencoded"}

    request, response = await app.asgi_client.post(
        "/", data=payload, headers=headers
    )

    assert request.form.get("test") == "OK"
    assert request.form.get("test") == "OK"  # For request.parsed_form


def test_post_form_urlencoded_keep_blanks(app):
    @app.route("/", methods=["POST"])
    async def handler(request):
        request.get_form(keep_blank_values=True)
        return text("OK")

    payload = "test="
    headers = {"content-type": "application/x-www-form-urlencoded"}

    request, response = app.test_client.post(
        "/", data=payload, headers=headers
    )

    assert request.form.get("test") == ""
    assert request.form.get("test") == ""  # For request.parsed_form


@pytest.mark.asyncio
async def test_post_form_urlencoded_keep_blanks_asgi(app):
    @app.route("/", methods=["POST"])
    async def handler(request):
        request.get_form(keep_blank_values=True)
        return text("OK")

    payload = "test="
    headers = {"content-type": "application/x-www-form-urlencoded"}

    request, response = await app.asgi_client.post(
        "/", data=payload, headers=headers
    )

    assert request.form.get("test") == ""
    assert request.form.get("test") == ""  # For request.parsed_form


def test_post_form_urlencoded_drop_blanks(app):
    @app.route("/", methods=["POST"])
    async def handler(request):
        return text("OK")

    payload = "test="
    headers = {"content-type": "application/x-www-form-urlencoded"}

    request, response = app.test_client.post(
        "/", data=payload, headers=headers
    )

    assert "test" not in request.form.keys()


@pytest.mark.asyncio
async def test_post_form_urlencoded_drop_blanks_asgi(app):
    @app.route("/", methods=["POST"])
    async def handler(request):
        return text("OK")

    payload = "test="
    headers = {"content-type": "application/x-www-form-urlencoded"}

    request, response = await app.asgi_client.post(
        "/", data=payload, headers=headers
    )

    assert "test" not in request.form.keys()


@pytest.mark.parametrize(
    "payload",
    [
        "------sanic\r\n"
        'Content-Disposition: form-data; name="test"\r\n'
        "\r\n"
        "OK\r\n"
        "------sanic--\r\n",
        "------sanic\r\n"
        'content-disposition: form-data; name="test"\r\n'
        "\r\n"
        "OK\r\n"
        "------sanic--\r\n",
    ],
)
def test_post_form_multipart_form_data(app, payload):
    @app.route("/", methods=["POST"])
    async def handler(request):
        return text("OK")

    headers = {"content-type": "multipart/form-data; boundary=----sanic"}

    request, response = app.test_client.post(data=payload, headers=headers)

    assert request.form.get("test") == "OK"


@pytest.mark.parametrize(
    "payload",
    [
        "------sanic\r\n"
        'Content-Disposition: form-data; name="test"\r\n'
        "\r\n"
        "OK\r\n"
        "------sanic--\r\n",
        "------sanic\r\n"
        'content-disposition: form-data; name="test"\r\n'
        "\r\n"
        "OK\r\n"
        "------sanic--\r\n",
    ],
)
@pytest.mark.asyncio
async def test_post_form_multipart_form_data_asgi(app, payload):
    @app.route("/", methods=["POST"])
    async def handler(request):
        return text("OK")

    headers = {"content-type": "multipart/form-data; boundary=----sanic"}

    request, response = await app.asgi_client.post(
        "/", data=payload, headers=headers
    )

    assert request.form.get("test") == "OK"


@pytest.mark.parametrize(
    "path,query,expected_url",
    [
        ("/foo", "", "http://{}:{}/foo"),
        ("/bar/baz", "", "http://{}:{}/bar/baz"),
        ("/moo/boo", "arg1=val1", "http://{}:{}/moo/boo?arg1=val1"),
    ],
)
def test_url_attributes_no_ssl(app, path, query, expected_url):
    async def handler(request):
        return text("OK")

    app.add_route(handler, path)

    request, response = app.test_client.get(path + f"?{query}")
    assert request.url == expected_url.format(HOST, request.server_port)

    parsed = urlparse(request.url)

    assert parsed.scheme == request.scheme
    assert parsed.path == request.path
    assert parsed.query == request.query_string
    assert parsed.netloc == request.host


@pytest.mark.parametrize(
    "path,query,expected_url",
    [
        ("/foo", "", "{}/foo"),
        ("/bar/baz", "", "{}/bar/baz"),
        ("/moo/boo", "arg1=val1", "{}/moo/boo?arg1=val1"),
    ],
)
@pytest.mark.asyncio
async def test_url_attributes_no_ssl_asgi(app, path, query, expected_url):
    async def handler(request):
        return text("OK")

    app.add_route(handler, path)

    request, response = await app.asgi_client.get(path + f"?{query}")
    assert request.url == expected_url.format(ASGI_BASE_URL)

    parsed = urlparse(request.url)

    assert parsed.scheme == request.scheme
    assert parsed.path == request.path
    assert parsed.query == request.query_string
    assert parsed.netloc == request.host


def test_form_with_multiple_values(app):
    @app.route("/", methods=["POST"])
    async def handler(request):
        return text("OK")

    payload = "selectedItems=v1&selectedItems=v2&selectedItems=v3"

    headers = {"content-type": "application/x-www-form-urlencoded"}

    request, response = app.test_client.post(
        "/", data=payload, headers=headers
    )

    assert request.form.getlist("selectedItems") == ["v1", "v2", "v3"]


@pytest.mark.asyncio
async def test_form_with_multiple_values_asgi(app):
    @app.route("/", methods=["POST"])
    async def handler(request):
        return text("OK")

    payload = "selectedItems=v1&selectedItems=v2&selectedItems=v3"

    headers = {"content-type": "application/x-www-form-urlencoded"}

    request, response = await app.asgi_client.post(
        "/", data=payload, headers=headers
    )

    assert request.form.getlist("selectedItems") == ["v1", "v2", "v3"]


def test_request_string_representation(app):
    @app.route("/", methods=["GET"])
    async def get(request):
        return text("OK")

    request, _ = app.test_client.get("/")
    assert repr(request) == "<Request: GET />"


@pytest.mark.asyncio
async def test_request_string_representation_asgi(app):
    @app.route("/", methods=["GET"])
    async def get(request):
        return text("OK")

    request, _ = await app.asgi_client.get("/")
    assert repr(request) == "<Request: GET />"


@pytest.mark.parametrize(
    "payload,filename",
    [
        (
            "------sanic\r\n"
            'Content-Disposition: form-data; filename="filename"; name="test"\r\n'
            "\r\n"
            "OK\r\n"
            "------sanic--\r\n",
            "filename",
        ),
        (
            "------sanic\r\n"
            'content-disposition: form-data; filename="filename"; name="test"\r\n'
            "\r\n"
            'content-type: application/json; {"field": "value"}\r\n'
            "------sanic--\r\n",
            "filename",
        ),
        (
            "------sanic\r\n"
            'Content-Disposition: form-data; filename=""; name="test"\r\n'
            "\r\n"
            "OK\r\n"
            "------sanic--\r\n",
            "",
        ),
        (
            "------sanic\r\n"
            'content-disposition: form-data; filename=""; name="test"\r\n'
            "\r\n"
            'content-type: application/json; {"field": "value"}\r\n'
            "------sanic--\r\n",
            "",
        ),
        (
            "------sanic\r\n"
            'Content-Disposition: form-data; filename*="utf-8\'\'filename_%C2%A0_test"; name="test"\r\n'
            "\r\n"
            "OK\r\n"
            "------sanic--\r\n",
            "filename_\u00A0_test",
        ),
        (
            "------sanic\r\n"
            'content-disposition: form-data; filename*="utf-8\'\'filename_%C2%A0_test"; name="test"\r\n'
            "\r\n"
            'content-type: application/json; {"field": "value"}\r\n'
            "------sanic--\r\n",
            "filename_\u00A0_test",
        ),
    ],
)
def test_request_multipart_files(app, payload, filename):
    @app.route("/", methods=["POST"])
    async def post(request):
        return text("OK")

    headers = {"content-type": "multipart/form-data; boundary=----sanic"}

    request, _ = app.test_client.post(data=payload, headers=headers)
    assert request.files.get("test").name == filename


@pytest.mark.parametrize(
    "payload,filename",
    [
        (
            "------sanic\r\n"
            'Content-Disposition: form-data; filename="filename"; name="test"\r\n'
            "\r\n"
            "OK\r\n"
            "------sanic--\r\n",
            "filename",
        ),
        (
            "------sanic\r\n"
            'content-disposition: form-data; filename="filename"; name="test"\r\n'
            "\r\n"
            'content-type: application/json; {"field": "value"}\r\n'
            "------sanic--\r\n",
            "filename",
        ),
        (
            "------sanic\r\n"
            'Content-Disposition: form-data; filename=""; name="test"\r\n'
            "\r\n"
            "OK\r\n"
            "------sanic--\r\n",
            "",
        ),
        (
            "------sanic\r\n"
            'content-disposition: form-data; filename=""; name="test"\r\n'
            "\r\n"
            'content-type: application/json; {"field": "value"}\r\n'
            "------sanic--\r\n",
            "",
        ),
        (
            "------sanic\r\n"
            'Content-Disposition: form-data; filename*="utf-8\'\'filename_%C2%A0_test"; name="test"\r\n'
            "\r\n"
            "OK\r\n"
            "------sanic--\r\n",
            "filename_\u00A0_test",
        ),
        (
            "------sanic\r\n"
            'content-disposition: form-data; filename*="utf-8\'\'filename_%C2%A0_test"; name="test"\r\n'
            "\r\n"
            'content-type: application/json; {"field": "value"}\r\n'
            "------sanic--\r\n",
            "filename_\u00A0_test",
        ),
    ],
)
@pytest.mark.asyncio
async def test_request_multipart_files_asgi(app, payload, filename):
    @app.route("/", methods=["POST"])
    async def post(request):
        return text("OK")

    headers = {"content-type": "multipart/form-data; boundary=----sanic"}

    request, _ = await app.asgi_client.post("/", data=payload, headers=headers)
    assert request.files.get("test").name == filename


def test_request_multipart_file_with_json_content_type(app):
    @app.route("/", methods=["POST"])
    async def post(request):
        return text("OK")

    payload = (
        "------sanic\r\n"
        'Content-Disposition: form-data; name="file"; filename="test.json"\r\n'
        "Content-Type: application/json\r\n"
        "Content-Length: 0"
        "\r\n"
        "\r\n"
        "------sanic--"
    )

    headers = {"content-type": "multipart/form-data; boundary=------sanic"}

    request, _ = app.test_client.post(data=payload, headers=headers)
    assert request.files.get("file").type == "application/json"


@pytest.mark.asyncio
async def test_request_multipart_file_with_json_content_type_asgi(app):
    @app.route("/", methods=["POST"])
    async def post(request):
        return text("OK")

    payload = (
        "------sanic\r\n"
        'Content-Disposition: form-data; name="file"; filename="test.json"\r\n'
        "Content-Type: application/json\r\n"
        "Content-Length: 0"
        "\r\n"
        "\r\n"
        "------sanic--"
    )

    headers = {"content-type": "multipart/form-data; boundary=------sanic"}

    request, _ = await app.asgi_client.post("/", data=payload, headers=headers)
    assert request.files.get("file").type == "application/json"


def test_request_multipart_file_without_field_name(app, caplog):
    @app.route("/", methods=["POST"])
    async def post(request):
        return text("OK")

    payload = (
        '------sanic\r\nContent-Disposition: form-data; filename="test.json"'
        "\r\nContent-Type: application/json\r\n\r\n\r\n------sanic--"
    )

    headers = {"content-type": "multipart/form-data; boundary=------sanic"}

    request, _ = app.test_client.post(
        data=payload, headers=headers, debug=True
    )
    with caplog.at_level(logging.DEBUG):
        request.form

    assert caplog.record_tuples[-1] == (
        "sanic.root",
        logging.DEBUG,
        "Form-data field does not have a 'name' parameter "
        "in the Content-Disposition header",
    )


def test_request_multipart_file_duplicate_filed_name(app):
    @app.route("/", methods=["POST"])
    async def post(request):
        return text("OK")

    payload = (
        "--e73ffaa8b1b2472b8ec848de833cb05b\r\n"
        'Content-Disposition: form-data; name="file"\r\n'
        "Content-Type: application/octet-stream\r\n"
        "Content-Length: 15\r\n"
        "\r\n"
        '{"test":"json"}\r\n'
        "--e73ffaa8b1b2472b8ec848de833cb05b\r\n"
        'Content-Disposition: form-data; name="file"\r\n'
        "Content-Type: application/octet-stream\r\n"
        "Content-Length: 15\r\n"
        "\r\n"
        '{"test":"json2"}\r\n'
        "--e73ffaa8b1b2472b8ec848de833cb05b--\r\n"
    )

    headers = {
        "Content-Type": "multipart/form-data; boundary=e73ffaa8b1b2472b8ec848de833cb05b"
    }

    request, _ = app.test_client.post(
        data=payload, headers=headers, debug=True
    )
    assert request.form.getlist("file") == [
        '{"test":"json"}',
        '{"test":"json2"}',
    ]


@pytest.mark.asyncio
async def test_request_multipart_file_duplicate_filed_name_asgi(app):
    @app.route("/", methods=["POST"])
    async def post(request):
        return text("OK")

    payload = (
        "--e73ffaa8b1b2472b8ec848de833cb05b\r\n"
        'Content-Disposition: form-data; name="file"\r\n'
        "Content-Type: application/octet-stream\r\n"
        "Content-Length: 15\r\n"
        "\r\n"
        '{"test":"json"}\r\n'
        "--e73ffaa8b1b2472b8ec848de833cb05b\r\n"
        'Content-Disposition: form-data; name="file"\r\n'
        "Content-Type: application/octet-stream\r\n"
        "Content-Length: 15\r\n"
        "\r\n"
        '{"test":"json2"}\r\n'
        "--e73ffaa8b1b2472b8ec848de833cb05b--\r\n"
    )

    headers = {
        "Content-Type": "multipart/form-data; boundary=e73ffaa8b1b2472b8ec848de833cb05b"
    }

    request, _ = await app.asgi_client.post("/", data=payload, headers=headers)
    assert request.form.getlist("file") == [
        '{"test":"json"}',
        '{"test":"json2"}',
    ]


def test_request_multipart_with_multiple_files_and_type(app):
    @app.route("/", methods=["POST"])
    async def post(request):
        return text("OK")

    payload = (
        '------sanic\r\nContent-Disposition: form-data; name="file"; filename="test.json"'
        "\r\nContent-Type: application/json\r\n\r\n\r\n"
        '------sanic\r\nContent-Disposition: form-data; name="file"; filename="some_file.pdf"\r\n'
        "Content-Type: application/pdf\r\n\r\n\r\n------sanic--"
    )
    headers = {"content-type": "multipart/form-data; boundary=------sanic"}

    request, _ = app.test_client.post(data=payload, headers=headers)
    assert len(request.files.getlist("file")) == 2
    assert request.files.getlist("file")[0].type == "application/json"
    assert request.files.getlist("file")[1].type == "application/pdf"


@pytest.mark.asyncio
async def test_request_multipart_with_multiple_files_and_type_asgi(app):
    @app.route("/", methods=["POST"])
    async def post(request):
        return text("OK")

    payload = (
        '------sanic\r\nContent-Disposition: form-data; name="file"; filename="test.json"'
        "\r\nContent-Type: application/json\r\n\r\n\r\n"
        '------sanic\r\nContent-Disposition: form-data; name="file"; filename="some_file.pdf"\r\n'
        "Content-Type: application/pdf\r\n\r\n\r\n------sanic--"
    )
    headers = {"content-type": "multipart/form-data; boundary=------sanic"}

    request, _ = await app.asgi_client.post("/", data=payload, headers=headers)
    assert len(request.files.getlist("file")) == 2
    assert request.files.getlist("file")[0].type == "application/json"
    assert request.files.getlist("file")[1].type == "application/pdf"


def test_request_repr(app):
    @app.get("/")
    def handler(request):
        return text("pass")

    request, response = app.test_client.get("/")
    assert repr(request) == "<Request: GET />"

    request.method = None
    assert repr(request) == "<Request: None />"


@pytest.mark.asyncio
async def test_request_repr_asgi(app):
    @app.get("/")
    def handler(request):
        return text("pass")

    request, response = await app.asgi_client.get("/")
    assert repr(request) == "<Request: GET />"

    request.method = None
    assert repr(request) == "<Request: None />"


def test_request_bool(app):
    @app.get("/")
    def handler(request):
        return text("pass")

    request, response = app.test_client.get("/")
    assert bool(request)


def test_request_parsing_form_failed(app, caplog):
    @app.route("/", methods=["POST"])
    async def handler(request):
        return text("OK")

    payload = "test=OK"
    headers = {"content-type": "multipart/form-data"}

    request, response = app.test_client.post(
        "/", data=payload, headers=headers
    )

    with caplog.at_level(logging.ERROR):
        request.form

    assert caplog.record_tuples[-1] == (
        "sanic.error",
        logging.ERROR,
        "Failed when parsing form",
    )


@pytest.mark.asyncio
async def test_request_parsing_form_failed_asgi(app, caplog):
    @app.route("/", methods=["POST"])
    async def handler(request):
        return text("OK")

    payload = "test=OK"
    headers = {"content-type": "multipart/form-data"}

    request, response = await app.asgi_client.post(
        "/", data=payload, headers=headers
    )

    with caplog.at_level(logging.ERROR):
        request.form

    assert caplog.record_tuples[-1] == (
        "sanic.error",
        logging.ERROR,
        "Failed when parsing form",
    )


def test_request_args_no_query_string(app):
    @app.get("/")
    def handler(request):
        return text("pass")

    request, response = app.test_client.get("/")

    assert request.args == {}


@pytest.mark.asyncio
async def test_request_args_no_query_string_await(app):
    @app.get("/")
    def handler(request):
        return text("pass")

    request, response = await app.asgi_client.get("/")

    assert request.args == {}


def test_request_query_args(app):
    # test multiple params with the same key
    params = [("test", "value1"), ("test", "value2")]

    @app.get("/")
    def handler(request):
        return text("pass")

    request, response = app.test_client.get("/", params=params)

    assert request.query_args == params

    # test cached value
    assert (
        request.parsed_not_grouped_args[(False, False, "utf-8", "replace")]
        == request.query_args
    )

    # test params directly in the url
    request, response = app.test_client.get("/?test=value1&test=value2")

    assert request.query_args == params

    # test unique params
    params = [("test1", "value1"), ("test2", "value2")]

    request, response = app.test_client.get("/", params=params)

    assert request.query_args == params

    # test no params
    request, response = app.test_client.get("/")

    assert not request.query_args


@pytest.mark.asyncio
async def test_request_query_args_asgi(app):
    # test multiple params with the same key
    params = [("test", "value1"), ("test", "value2")]

    @app.get("/")
    def handler(request):
        return text("pass")

    request, response = await app.asgi_client.get("/", params=params)

    assert request.query_args == params

    # test cached value
    assert (
        request.parsed_not_grouped_args[(False, False, "utf-8", "replace")]
        == request.query_args
    )

    # test params directly in the url
    request, response = await app.asgi_client.get("/?test=value1&test=value2")

    assert request.query_args == params

    # test unique params
    params = [("test1", "value1"), ("test2", "value2")]

    request, response = await app.asgi_client.get("/", params=params)

    assert request.query_args == params

    # test no params
    request, response = await app.asgi_client.get("/")

    assert not request.query_args


def test_request_query_args_custom_parsing(app):
    @app.get("/")
    def handler(request):
        return text("pass")

    request, response = app.test_client.get(
        "/?test1=value1&test2=&test3=value3"
    )

    assert request.get_query_args(keep_blank_values=True) == [
        ("test1", "value1"),
        ("test2", ""),
        ("test3", "value3"),
    ]
    assert request.query_args == [("test1", "value1"), ("test3", "value3")]
    assert request.get_query_args(keep_blank_values=False) == [
        ("test1", "value1"),
        ("test3", "value3"),
    ]

    assert request.get_args(keep_blank_values=True) == RequestParameters(
        {"test1": ["value1"], "test2": [""], "test3": ["value3"]}
    )

    assert request.args == RequestParameters(
        {"test1": ["value1"], "test3": ["value3"]}
    )

    assert request.get_args(keep_blank_values=False) == RequestParameters(
        {"test1": ["value1"], "test3": ["value3"]}
    )


@pytest.mark.asyncio
async def test_request_query_args_custom_parsing_asgi(app):
    @app.get("/")
    def handler(request):
        return text("pass")

    request, response = await app.asgi_client.get(
        "/?test1=value1&test2=&test3=value3"
    )

    assert request.get_query_args(keep_blank_values=True) == [
        ("test1", "value1"),
        ("test2", ""),
        ("test3", "value3"),
    ]
    assert request.query_args == [("test1", "value1"), ("test3", "value3")]
    assert request.get_query_args(keep_blank_values=False) == [
        ("test1", "value1"),
        ("test3", "value3"),
    ]

    assert request.get_args(keep_blank_values=True) == RequestParameters(
        {"test1": ["value1"], "test2": [""], "test3": ["value3"]}
    )

    assert request.args == RequestParameters(
        {"test1": ["value1"], "test3": ["value3"]}
    )

    assert request.get_args(keep_blank_values=False) == RequestParameters(
        {"test1": ["value1"], "test3": ["value3"]}
    )


def test_request_cookies(app):
    cookies = {"test": "OK"}

    @app.get("/")
    def handler(request):
        return text("OK")

    request, response = app.test_client.get("/", cookies=cookies)

    assert request.cookies == cookies
    assert request.cookies == cookies  # For request._cookies


@pytest.mark.asyncio
async def test_request_cookies_asgi(app):
    cookies = {"test": "OK"}

    @app.get("/")
    def handler(request):
        return text("OK")

    request, response = await app.asgi_client.get("/", cookies=cookies)

    assert request.cookies == cookies
    assert request.cookies == cookies  # For request._cookies


def test_request_cookies_without_cookies(app):
    @app.get("/")
    def handler(request):
        return text("OK")

    request, response = app.test_client.get("/")

    assert request.cookies == {}


@pytest.mark.asyncio
async def test_request_cookies_without_cookies_asgi(app):
    @app.get("/")
    def handler(request):
        return text("OK")

    request, response = await app.asgi_client.get("/")

    assert request.cookies == {}


def test_request_port(app):
    @app.get("/")
    def handler(request):
        return text("OK")

    request, response = app.test_client.get("/")

    port = request.port
    assert isinstance(port, int)


@pytest.mark.asyncio
async def test_request_port_asgi(app):
    @app.get("/")
    def handler(request):
        return text("OK")

    request, response = await app.asgi_client.get("/")

    port = request.port
    assert isinstance(port, int)


def test_request_socket(app):
    @app.get("/")
    def handler(request):
        return text("OK")

    request, response = app.test_client.get("/")

    socket = request.socket
    assert isinstance(socket, tuple)

    ip = socket[0]
    port = socket[1]

    assert ip == request.ip
    assert port == request.port


def test_request_server_name(app):
    @app.get("/")
    def handler(request):
        return text("OK")

    request, response = app.test_client.get("/")
    assert request.server_name == "127.0.0.1"


def test_request_server_name_in_host_header(app):
    @app.get("/")
    def handler(request):
        return text("OK")

    request, response = app.test_client.get(
        "/", headers={"Host": "my-server:5555"}
    )
    assert request.server_name == "my-server"

    request, response = app.test_client.get(
        "/", headers={"Host": "[2a00:1450:400f:80c::200e]:5555"}
    )
    assert request.server_name == "[2a00:1450:400f:80c::200e]"

    request, response = app.test_client.get(
        "/", headers={"Host": "mal_formed"}
    )
    assert request.server_name == ""


def test_request_server_name_forwarded(app):
    @app.get("/")
    def handler(request):
        return text("OK")

    app.config.PROXIES_COUNT = 1
    request, response = app.test_client.get(
        "/",
        headers={
            "Host": "my-server:5555",
            "X-Forwarded-For": "127.1.2.3",
            "X-Forwarded-Host": "your-server",
        },
    )
    assert request.server_name == "your-server"


def test_request_server_port(app):
    @app.get("/")
    def handler(request):
        return text("OK")

    test_client = SanicTestClient(app)
    request, response = test_client.get("/", headers={"Host": "my-server"})
    assert request.server_port == 80


def test_request_server_port_in_host_header(app):
    @app.get("/")
    def handler(request):
        return text("OK")

    request, response = app.test_client.get(
        "/", headers={"Host": "my-server:5555"}
    )
    assert request.server_port == 5555

    request, response = app.test_client.get(
        "/", headers={"Host": "[2a00:1450:400f:80c::200e]:5555"}
    )
    assert request.server_port == 5555

    request, response = app.test_client.get(
        "/", headers={"Host": "mal_formed:5555"}
    )
    if PORT is None:
        assert request.server_port != 5555
    else:
        assert request.server_port == app.test_client.port


def test_request_server_port_forwarded(app):
    @app.get("/")
    def handler(request):
        return text("OK")

    app.config.PROXIES_COUNT = 1
    request, response = app.test_client.get(
        "/",
        headers={
            "Host": "my-server:5555",
            "X-Forwarded-For": "127.1.2.3",
            "X-Forwarded-Port": "4444",
        },
    )
    assert request.server_port == 4444


def test_request_form_invalid_content_type(app):
    @app.route("/", methods=["POST"])
    async def post(request):
        return text("OK")

    request, response = app.test_client.post("/", json={"test": "OK"})

    assert request.form == {}


def test_server_name_and_url_for(app):
    @app.get("/foo")
    def handler(request):
        return text("ok")

    app.config.SERVER_NAME = "my-server"  # This means default port
    assert app.url_for("handler", _external=True) == "http://my-server/foo"
    request, response = app.test_client.get("/foo")
    assert request.url_for("handler") == f"http://my-server/foo"

    app.config.SERVER_NAME = "https://my-server/path"
    request, response = app.test_client.get("/foo")
    url = f"https://my-server/path/foo"
    assert app.url_for("handler", _external=True) == url
    assert request.url_for("handler") == url


def test_url_for_with_forwarded_request(app):
    @app.get("/")
    def handler(request):
        return text("OK")

    @app.get("/another_view/")
    def view_name(request):
        return text("OK")

    app.config.SERVER_NAME = "my-server"
    app.config.PROXIES_COUNT = 1
    request, response = app.test_client.get(
        "/",
        headers={
            "X-Forwarded-For": "127.1.2.3",
            "X-Forwarded-Proto": "https",
            "X-Forwarded-Port": "6789",
        },
    )
    assert app.url_for("view_name") == "/another_view"
    assert (
        app.url_for("view_name", _external=True)
        == "http://my-server/another_view"
    )
    assert (
        request.url_for("view_name") == "https://my-server:6789/another_view"
    )

    request, response = app.test_client.get(
        "/",
        headers={
            "X-Forwarded-For": "127.1.2.3",
            "X-Forwarded-Proto": "https",
            "X-Forwarded-Port": "443",
        },
    )
    assert request.url_for("view_name") == "https://my-server/another_view"


@pytest.mark.asyncio
async def test_request_form_invalid_content_type_asgi(app):
    @app.route("/", methods=["POST"])
    async def post(request):
        return text("OK")

    request, response = await app.asgi_client.post("/", json={"test": "OK"})

    assert request.form == {}


def test_endpoint_basic():
    app = Sanic(name="Test")

    @app.route("/")
    def my_unique_handler(request):
        return text("Hello")

    request, response = app.test_client.get("/")

    assert request.endpoint == "Test.my_unique_handler"


@pytest.mark.asyncio
async def test_endpoint_basic_asgi():
    app = Sanic(name="Test")

    @app.route("/")
    def my_unique_handler(request):
        return text("Hello")

    request, response = await app.asgi_client.get("/")

    assert request.endpoint == "Test.my_unique_handler"


def test_endpoint_named_app():
    app = Sanic("named")

    @app.route("/")
    def my_unique_handler(request):
        return text("Hello")

    request, response = app.test_client.get("/")

    assert request.endpoint == "named.my_unique_handler"


@pytest.mark.asyncio
async def test_endpoint_named_app_asgi():
    app = Sanic("named")

    @app.route("/")
    def my_unique_handler(request):
        return text("Hello")

    request, response = await app.asgi_client.get("/")

    assert request.endpoint == "named.my_unique_handler"


def test_endpoint_blueprint():
    bp = Blueprint("my_blueprint", url_prefix="/bp")

    @bp.route("/")
    async def bp_root(request):
        return text("Hello")

    app = Sanic("named")
    app.blueprint(bp)

    request, response = app.test_client.get("/bp")

    assert request.endpoint == "named.my_blueprint.bp_root"


@pytest.mark.asyncio
async def test_endpoint_blueprint_asgi():
    bp = Blueprint("my_blueprint", url_prefix="/bp")

    @bp.route("/")
    async def bp_root(request):
        return text("Hello")

    app = Sanic("named")
    app.blueprint(bp)

    request, response = await app.asgi_client.get("/bp")

    assert request.endpoint == "named.my_blueprint.bp_root"


def test_url_for_without_server_name(app):
    @app.route("/sample")
    def sample(request):
        return json({"url": request.url_for("url_for")})

    @app.route("/url-for")
    def url_for(request):
        return text("url-for")

    request, response = app.test_client.get("/sample")
    assert (
        response.json["url"]
        == f"http://127.0.0.1:{request.server_port}/url-for"
    )


def test_safe_method_with_body_ignored(app):
    @app.get("/")
    async def handler(request):
        return text("OK")

    payload = {"test": "OK"}
    headers = {"content-type": "application/json"}

    request, response = app.test_client.request(
        "/", http_method="get", data=json_dumps(payload), headers=headers
    )

    assert request.body == b""
    assert request.json == None
    assert response.body == b"OK"


def test_safe_method_with_body(app):
    @app.get("/", ignore_body=False)
    async def handler(request):
        return text("OK")

    payload = {"test": "OK"}
    headers = {"content-type": "application/json"}
    data = json_dumps(payload)
    request, response = app.test_client.request(
        "/", http_method="get", data=data, headers=headers
    )

    assert request.body == data.encode("utf-8")
    assert request.json.get("test") == "OK"
    assert response.body == b"OK"


def test_conflicting_body_methods_overload(app):
    @app.put("/")
    @app.put("/p/")
    @app.put("/p/<foo>")
    async def put(request, foo=None):
        return json(
            {"name": request.route.name, "body": str(request.body), "foo": foo}
        )

    @app.delete("/p/<foo>")
    async def delete(request, foo):
        return json(
            {"name": request.route.name, "body": str(request.body), "foo": foo}
        )

    payload = {"test": "OK"}
    data = str(json_dumps(payload).encode())

    _, response = app.test_client.put("/", json=payload)
    assert response.status == 200
    assert response.json == {
        "name": "test_conflicting_body_methods_overload.put",
        "foo": None,
        "body": data,
    }
    _, response = app.test_client.put("/p", json=payload)
    assert response.status == 200
    assert response.json == {
        "name": "test_conflicting_body_methods_overload.put",
        "foo": None,
        "body": data,
    }
    _, response = app.test_client.put("/p/test", json=payload)
    assert response.status == 200
    assert response.json == {
        "name": "test_conflicting_body_methods_overload.put",
        "foo": "test",
        "body": data,
    }
    _, response = app.test_client.delete("/p/test")
    assert response.status == 200
    assert response.json == {
        "name": "test_conflicting_body_methods_overload.delete",
        "foo": "test",
        "body": str("".encode()),
    }


def test_handler_overload(app):
    @app.get("/long/sub/route/param_a/<param_a:str>/param_b/<param_b:str>")
    @app.post("/long/sub/route/")
    def handler(request, **kwargs):
        return json(kwargs)

    _, response = app.test_client.get(
        "/long/sub/route/param_a/foo/param_b/bar"
    )
    assert response.status == 200
    assert response.json == {
        "param_a": "foo",
        "param_b": "bar",
    }
    _, response = app.test_client.post("/long/sub/route")
    assert response.status == 200
    assert response.json == {}
