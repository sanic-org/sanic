from datetime import datetime, timedelta
from http.cookies import SimpleCookie
from unittest.mock import Mock

import pytest

from sanic import Request, Sanic
from sanic.compat import Header
from sanic.cookies import Cookie, CookieJar
from sanic.cookies.request import CookieRequestParameters, parse_cookie
from sanic.exceptions import ServerError
from sanic.response import text
from sanic.response.convenience import json


def test_request_cookies():
    cdict = parse_cookie("foo=one; foo=two; abc = xyz;;bare;=bare2")
    assert cdict == {
        "foo": ["one", "two"],
        "abc": ["xyz"],
        "": ["bare", "bare2"],
    }
    c = CookieRequestParameters(cdict)
    assert c.getlist("foo") == ["one", "two"]
    assert c.getlist("abc") == ["xyz"]
    assert c.getlist("") == ["bare", "bare2"]
    assert c.getlist("bare") == []


# ------------------------------------------------------------ #
#  GET
# ------------------------------------------------------------ #


def test_cookies(app):
    @app.route("/")
    def handler(request):
        cookie_value = request.cookies["test"]
        response = text(f"Cookies are: {cookie_value}")
        response.cookies["right_back"] = "at you"
        return response

    request, response = app.test_client.get("/", cookies={"test": "working!"})
    response_cookies = SimpleCookie()
    response_cookies.load(response.headers.get("Set-Cookie", {}))

    assert response.text == "Cookies are: working!"
    assert response_cookies["right_back"].value == "at you"


@pytest.mark.asyncio
async def test_cookies_asgi(app):
    @app.route("/")
    def handler(request):
        cookie_value = request.cookies["test"]
        response = text(f"Cookies are: {cookie_value}")
        response.cookies["right_back"] = "at you"
        return response

    request, response = await app.asgi_client.get(
        "/", cookies={"test": "working!"}
    )
    response_cookies = SimpleCookie()
    response_cookies.load(response.headers.get("set-cookie", {}))

    assert response.body == b"Cookies are: working!"
    assert response_cookies["right_back"].value == "at you"


@pytest.mark.parametrize("httponly,expected", [(False, False), (True, True)])
def test_false_cookies_encoded(app, httponly, expected):
    @app.route("/")
    def handler(request):
        response = text("hello cookies")
        response.cookies["hello"] = "world"
        response.cookies["hello"]["httponly"] = httponly
        return text(response.cookies["hello"].encode("utf8").decode())

    request, response = app.test_client.get("/")

    assert ("HttpOnly" in response.text) == expected


@pytest.mark.parametrize("httponly,expected", [(False, False), (True, True)])
def test_false_cookies(app, httponly, expected):
    @app.route("/")
    def handler(request):
        response = text("hello cookies")
        response.cookies["right_back"] = "at you"
        response.cookies["right_back"]["httponly"] = httponly
        return response

    request, response = app.test_client.get("/")
    response_cookies = SimpleCookie()
    response_cookies.load(response.headers.get("Set-Cookie", {}))

    assert ("HttpOnly" in response_cookies["right_back"].output()) == expected


def test_http2_cookies(app):
    @app.route("/")
    async def handler(request):
        cookie_value = request.cookies["test"]
        response = text(f"Cookies are: {cookie_value}")
        return response

    headers = {"cookie": "test=working!"}
    request, response = app.test_client.get("/", headers=headers)

    assert response.text == "Cookies are: working!"


def test_cookie_options(app):
    @app.route("/")
    def handler(request):
        response = text("OK")
        response.cookies["test"] = "at you"
        response.cookies["test"]["httponly"] = True
        response.cookies["test"]["expires"] = datetime.now() + timedelta(
            seconds=10
        )
        return response

    request, response = app.test_client.get("/")
    response_cookies = SimpleCookie()
    response_cookies.load(response.headers.get("Set-Cookie", {}))

    assert response_cookies["test"].value == "at you"
    assert response_cookies["test"]["httponly"] is True


def test_cookie_deletion(app):
    cookie_jar = None

    @app.route("/")
    def handler(request):
        nonlocal cookie_jar
        response = text("OK")
        del response.cookies["one"]
        response.cookies["two"] = "testing"
        del response.cookies["two"]
        cookie_jar = response.cookies
        return response

    _, response = app.test_client.get("/")

    assert cookie_jar.get_cookie("one").max_age == 0
    assert cookie_jar.get_cookie("two").max_age == 0
    assert len(response.cookies) == 0


def test_cookie_reserved_cookie():
    with pytest.raises(expected_exception=KeyError) as e:
        Cookie("domain", "testdomain.com")
        assert e.message == "Cookie name is a reserved word"


def test_cookie_illegal_key_format():
    with pytest.raises(expected_exception=KeyError) as e:
        Cookie("testå", "test")
        assert e.message == "Cookie key contains illegal characters"


def test_cookie_set_unknown_property():
    c = Cookie("test_cookie", "value")
    with pytest.raises(expected_exception=KeyError) as e:
        c["invalid"] = "value"
        assert e.message == "Unknown cookie property"


def test_cookie_set_same_key(app):
    cookies = {"test": "wait"}

    @app.get("/")
    def handler(request):
        response = text("pass")
        response.cookies["test"] = "modified"
        response.cookies["test"] = "pass"
        return response

    request, response = app.test_client.get("/", cookies=cookies)
    assert response.status == 200
    assert response.cookies["test"] == "pass"


@pytest.mark.parametrize("max_age", ["0", 30, "30"])
def test_cookie_max_age(app, max_age):
    cookies = {"test": "wait"}

    @app.get("/")
    def handler(request):
        response = text("pass")
        response.cookies["test"] = "pass"
        response.cookies["test"]["max-age"] = max_age
        return response

    request, response = app.test_client.get(
        "/", cookies=cookies, raw_cookies=True
    )
    assert response.status == 200

    cookie = response.cookies.get("test")
    if (
        str(max_age).isdigit()
        and int(max_age) == float(max_age)
        and int(max_age) != 0
    ):
        cookie_expires = datetime.utcfromtimestamp(
            response.raw_cookies["test"].expires
        ).replace(microsecond=0)

        # Grabbing utcnow after the response may lead to it being off slightly.
        # Therefore, we 0 out the microseconds, and accept the test if there
        # is a 1 second difference.
        expires = datetime.utcnow().replace(microsecond=0) + timedelta(
            seconds=int(max_age)
        )

        assert cookie == "pass"
        assert (
            cookie_expires == expires
            or cookie_expires == expires + timedelta(seconds=-1)
        )
    else:
        assert cookie is None


@pytest.mark.parametrize("max_age", [30.0, 30.1, "test"])
def test_cookie_bad_max_age(app, max_age):
    cookies = {"test": "wait"}

    @app.get("/")
    def handler(request):
        response = text("pass")
        response.cookies["test"] = "pass"
        response.cookies["test"]["max-age"] = max_age
        return response

    request, response = app.test_client.get(
        "/", cookies=cookies, raw_cookies=True
    )
    assert response.status == 500


@pytest.mark.parametrize("expires", [timedelta(seconds=60)])
def test_cookie_expires(app: Sanic, expires: timedelta):
    expires_time = datetime.utcnow().replace(microsecond=0) + expires
    cookies = {"test": "wait"}

    @app.get("/")
    def handler(request):
        response = text("pass")
        response.cookies["test"] = "pass"
        response.cookies["test"]["expires"] = expires_time
        return response

    request, response = app.test_client.get(
        "/", cookies=cookies, raw_cookies=True
    )

    cookie_expires = datetime.utcfromtimestamp(
        response.raw_cookies["test"].expires
    ).replace(microsecond=0)

    assert response.status == 200
    assert response.cookies["test"] == "pass"
    assert cookie_expires == expires_time


@pytest.mark.parametrize("expires", ["Fri, 21-Dec-2018 15:30:00 GMT"])
def test_cookie_expires_illegal_instance_type(expires):
    c = Cookie("test_cookie", "value")
    with pytest.raises(expected_exception=TypeError) as e:
        c["expires"] = expires
        assert e.message == "Cookie 'expires' property must be a datetime"


@pytest.mark.parametrize("value", ("foo=one; foo=two", "foo=one;foo=two"))
def test_request_with_duplicate_cookie_key(value):
    headers = Header({"Cookie": value})
    request = Request(b"/", headers, "1.1", "GET", Mock(), Mock())

    assert request.cookies["foo"] == "one"
    assert request.cookies.get("foo") == "one"
    assert request.cookies.getlist("foo") == ["one", "two"]
    assert request.cookies.get("bar") is None


def test_cookie_jar_cookies():
    headers = Header()
    jar = CookieJar(headers)
    jar.add_cookie("foo", "one")
    jar.add_cookie("foo", "two", domain="example.com")

    assert len(jar.cookies) == 2
    assert len(headers) == 2


def test_cookie_jar_has_cookie():
    headers = Header()
    jar = CookieJar(headers)
    jar.add_cookie("foo", "one")
    jar.add_cookie("foo", "two", domain="example.com")

    assert jar.has_cookie("foo")
    assert jar.has_cookie("foo", domain="example.com")
    assert not jar.has_cookie("foo", path="/unknown")
    assert not jar.has_cookie("bar")


def test_cookie_jar_get_cookie():
    headers = Header()
    jar = CookieJar(headers)
    cookie1 = jar.add_cookie("foo", "one")
    cookie2 = jar.add_cookie("foo", "two", domain="example.com")

    assert jar.get_cookie("foo") is cookie1
    assert jar.get_cookie("foo", domain="example.com") is cookie2
    assert jar.get_cookie("foo", path="/unknown") is None
    assert jar.get_cookie("bar") is None


def test_cookie_jar_add_cookie_encode():
    headers = Header()
    jar = CookieJar(headers)
    jar.add_cookie("foo", "one")
    jar.add_cookie(
        "foo",
        "two",
        domain="example.com",
        path="/something",
        secure=True,
        max_age=999,
        httponly=True,
        samesite="strict",
    )
    jar.add_cookie("foo", "three", secure_prefix=True)
    jar.add_cookie("foo", "four", host_prefix=True)
    jar.add_cookie("foo", "five", host_prefix=True, partitioned=True)

    encoded = [cookie.encode("ascii") for cookie in jar.cookies]
    assert encoded == [
        b"foo=one; Path=/; SameSite=Lax; Secure",
        b"foo=two; Path=/something; Domain=example.com; Max-Age=999; SameSite=Strict; Secure; HttpOnly",  # noqa
        b"__Secure-foo=three; Path=/; SameSite=Lax; Secure",
        b"__Host-foo=four; Path=/; SameSite=Lax; Secure",
        b"__Host-foo=five; Path=/; SameSite=Lax; Secure; Partitioned",
    ]


def test_cookie_jar_old_school_cookie_encode():
    headers = Header()
    jar = CookieJar(headers)
    jar["foo"] = "one"
    jar["bar"] = "two"
    jar["bar"]["domain"] = "example.com"
    jar["bar"]["path"] = "/something"
    jar["bar"]["secure"] = True
    jar["bar"]["max-age"] = 999
    jar["bar"]["httponly"] = True
    jar["bar"]["samesite"] = "strict"

    encoded = [cookie.encode("ascii") for cookie in jar.cookies]
    assert encoded == [
        b"foo=one; Path=/",
        b"bar=two; Path=/something; Domain=example.com; Max-Age=999; SameSite=Strict; Secure; HttpOnly",  # noqa
    ]


def test_cookie_jar_delete_cookie_encode():
    headers = Header()
    jar = CookieJar(headers)
    jar.delete_cookie("foo")
    jar.delete_cookie("foo", domain="example.com")

    encoded = [cookie.encode("ascii") for cookie in jar.cookies]
    assert encoded == [
        b'foo=""; Path=/; Max-Age=0; Secure',
        b'foo=""; Path=/; Domain=example.com; Max-Age=0; Secure',
    ]


def test_cookie_jar_delete_nonsecure_cookie():
    headers = Header()
    jar = CookieJar(headers)
    jar.delete_cookie("foo", domain="example.com", secure=False)

    encoded = [cookie.encode("ascii") for cookie in jar.cookies]
    assert encoded == [
        b'foo=""; Path=/; Domain=example.com; Max-Age=0',
    ]


def test_cookie_jar_delete_existing_cookie():
    headers = Header()
    jar = CookieJar(headers)
    jar.add_cookie(
        "foo", "test", secure=True, domain="example.com", samesite="Strict"
    )
    jar.delete_cookie("foo", domain="example.com", secure=True)

    encoded = [cookie.encode("ascii") for cookie in jar.cookies]
    # deletion cookie contains samesite=Strict as was in original cookie
    assert encoded == [
        b'foo=""; Path=/; Domain=example.com; Max-Age=0; SameSite=Strict; Secure',
    ]


def test_cookie_jar_delete_existing_nonsecure_cookie():
    headers = Header()
    jar = CookieJar(headers)
    jar.add_cookie(
        "foo", "test", secure=False, domain="example.com", samesite="Strict"
    )
    jar.delete_cookie("foo", domain="example.com", secure=False)

    encoded = [cookie.encode("ascii") for cookie in jar.cookies]
    # deletion cookie contains samesite=Strict as was in original cookie
    assert encoded == [
        b'foo=""; Path=/; Domain=example.com; Max-Age=0; SameSite=Strict',
    ]


def test_cookie_jar_delete_existing_nonsecure_cookie_bad_prefix():
    headers = Header()
    jar = CookieJar(headers)
    jar.add_cookie(
        "foo", "test", secure=False, domain="example.com", samesite="Strict"
    )
    message = (
        "Cannot set host_prefix on a cookie without "
        "path='/', domain=None, and secure=True"
    )
    with pytest.raises(ServerError, match=message):
        jar.delete_cookie(
            "foo",
            domain="example.com",
            secure=False,
            secure_prefix=True,
            host_prefix=True,
        )


def test_cookie_jar_old_school_delete_encode():
    headers = Header()
    jar = CookieJar(headers)
    del jar["foo"]

    encoded = [cookie.encode("ascii") for cookie in jar.cookies]
    assert encoded == [
        b'foo=""; Path=/; Max-Age=0; Secure',
    ]


def test_bad_cookie_prarms():
    headers = Header()
    jar = CookieJar(headers)

    with pytest.raises(
        ServerError,
        match=(
            "Both host_prefix and secure_prefix were requested. "
            "A cookie should have only one prefix."
        ),
    ):
        jar.add_cookie("foo", "bar", host_prefix=True, secure_prefix=True)

    with pytest.raises(
        ServerError,
        match="Cannot set host_prefix on a cookie without secure=True",
    ):
        jar.add_cookie("foo", "bar", host_prefix=True, secure=False)

    with pytest.raises(
        ServerError,
        match="Cannot set host_prefix on a cookie unless path='/'",
    ):
        jar.add_cookie(
            "foo", "bar", host_prefix=True, secure=True, path="/foo"
        )

    with pytest.raises(
        ServerError,
        match="Cannot set host_prefix on a cookie with a defined domain",
    ):
        jar.add_cookie(
            "foo", "bar", host_prefix=True, secure=True, domain="foo.bar"
        )

    with pytest.raises(
        ServerError,
        match="Cannot set secure_prefix on a cookie without secure=True",
    ):
        jar.add_cookie("foo", "bar", secure_prefix=True, secure=False)

    with pytest.raises(
        ServerError,
        match=(
            "Cannot create a partitioned cookie without "
            "also setting host_prefix=True"
        ),
    ):
        jar.add_cookie("foo", "bar", partitioned=True)


def test_cookie_accessors(app: Sanic):
    @app.get("/")
    async def handler(request: Request):
        return json(
            {
                "getitem": {
                    "one": request.cookies["one"],
                    "two": request.cookies["two"],
                    "three": request.cookies["three"],
                },
                "get": {
                    "one": request.cookies.get("one", "fallback"),
                    "two": request.cookies.get("two", "fallback"),
                    "three": request.cookies.get("three", "fallback"),
                    "four": request.cookies.get("four", "fallback"),
                },
                "getlist": {
                    "one": request.cookies.getlist("one"),
                    "two": request.cookies.getlist("two"),
                    "three": request.cookies.getlist("three"),
                    "four": request.cookies.getlist("four"),
                    "five": request.cookies.getlist("five", ["fallback"]),
                },
                "getattr": {
                    "one": request.cookies.one,
                    "two": request.cookies.two,
                    "three": request.cookies.three,
                    "four": request.cookies.four,
                },
            }
        )

    _, response = app.test_client.get(
        "/",
        cookies={
            "__Host-one": "1",
            "__Secure-two": "2",
            "three": "3",
        },
    )

    assert response.json == {
        "getitem": {
            "one": "1",
            "two": "2",
            "three": "3",
        },
        "get": {
            "one": "1",
            "two": "2",
            "three": "3",
            "four": "fallback",
        },
        "getlist": {
            "one": ["1"],
            "two": ["2"],
            "three": ["3"],
            "four": [],
            "five": ["fallback"],
        },
        "getattr": {
            "one": "1",
            "two": "2",
            "three": "3",
            "four": "",
        },
    }


def test_cookie_accessor_hyphens():
    cookies = CookieRequestParameters({"session-token": ["abc123"]})

    assert cookies.get("session-token") == cookies.session_token


def test_cookie_passthru(app):
    cookie_jar = None

    @app.route("/")
    def handler(request):
        nonlocal cookie_jar
        response = text("OK")
        response.add_cookie("one", "1", host_prefix=True)
        response.delete_cookie("two", secure_prefix=True)
        cookie_jar = response.cookies
        return response

    _, response = app.test_client.get("/")

    assert cookie_jar.get_cookie("two", secure_prefix=True).max_age == 0
    assert len(response.cookies) == 1
    assert response.cookies["__Host-one"] == "1"
