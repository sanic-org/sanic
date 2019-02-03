from datetime import datetime, timedelta
from http.cookies import SimpleCookie
from sanic.response import text
import pytest
from sanic.cookies import Cookie, DEFAULT_MAX_AGE

# ------------------------------------------------------------ #
#  GET
# ------------------------------------------------------------ #


def test_cookies(app):
    @app.route("/")
    def handler(request):
        response = text("Cookies are: {}".format(request.cookies["test"]))
        response.cookies["right_back"] = "at you"
        return response

    request, response = app.test_client.get("/", cookies={"test": "working!"})
    response_cookies = SimpleCookie()
    response_cookies.load(response.headers.get("Set-Cookie", {}))

    assert response.text == "Cookies are: working!"
    assert response_cookies["right_back"].value == "at you"


@pytest.mark.parametrize("httponly,expected", [(False, False), (True, True)])
def test_false_cookies_encoded(app, httponly, expected):
    @app.route("/")
    def handler(request):
        response = text("hello cookies")
        response.cookies["hello"] = "world"
        response.cookies["hello"]["httponly"] = httponly
        return text(response.cookies["hello"].encode("utf8"))

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
        response = text("Cookies are: {}".format(request.cookies["test"]))
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
    @app.route("/")
    def handler(request):
        response = text("OK")
        del response.cookies["i_want_to_die"]
        response.cookies["i_never_existed"] = "testing"
        del response.cookies["i_never_existed"]
        return response

    request, response = app.test_client.get("/")
    response_cookies = SimpleCookie()
    response_cookies.load(response.headers.get("Set-Cookie", {}))

    assert int(response_cookies["i_want_to_die"]["max-age"]) == 0
    with pytest.raises(KeyError):
        response.cookies["i_never_existed"]


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
    assert response.cookies["test"].value == "pass"


@pytest.mark.parametrize("max_age", ["0", 30, 30.0, 30.1, "30", "test"])
def test_cookie_max_age(app, max_age):
    cookies = {"test": "wait"}

    @app.get("/")
    def handler(request):
        response = text("pass")
        response.cookies["test"] = "pass"
        response.cookies["test"]["max-age"] = max_age
        return response

    request, response = app.test_client.get("/", cookies=cookies)
    assert response.status == 200

    assert response.cookies["test"].value == "pass"

    if str(max_age).isdigit() and int(max_age) == float(max_age):
        assert response.cookies["test"]["max-age"] == str(max_age)
    else:
        assert response.cookies["test"]["max-age"] == str(DEFAULT_MAX_AGE)


@pytest.mark.parametrize(
    "expires",
    [datetime.now() + timedelta(seconds=60)],
)
def test_cookie_expires(app, expires):
    cookies = {"test": "wait"}

    @app.get("/")
    def handler(request):
        response = text("pass")
        response.cookies["test"] = "pass"
        response.cookies["test"]["expires"] = expires
        return response

    request, response = app.test_client.get("/", cookies=cookies)
    assert response.status == 200

    assert response.cookies["test"].value == "pass"

    if isinstance(expires, datetime):
        expires = expires.strftime("%a, %d-%b-%Y %T GMT")

    assert response.cookies["test"]["expires"] == expires


@pytest.mark.parametrize(
    "expires",
    ["Fri, 21-Dec-2018 15:30:00 GMT"],
)
def test_cookie_expires_illegal_instance_type(expires):
    c = Cookie("test_cookie", "value")
    with pytest.raises(expected_exception=KeyError) as e:
        c["expires"] = expires
        assert e.message == "Cookie 'expires' property must be a datetime instance"
