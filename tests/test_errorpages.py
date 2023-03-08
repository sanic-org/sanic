import logging

import pytest

from sanic import Sanic
from sanic.config import Config
from sanic.errorpages import TextRenderer, exception_response, guess_mime
from sanic.exceptions import NotFound, SanicException
from sanic.handlers import ErrorHandler
from sanic.request import Request
from sanic.response import HTTPResponse, empty, html, json, text


@pytest.fixture
def app():
    app = Sanic("error_page_testing")

    @app.route("/error", methods=["GET", "POST"])
    def err(request):
        raise Exception("something went wrong")

    @app.get("/forced_json/<fail>", error_format="json")
    def manual_fail(request, fail):
        if fail == "fail":
            raise Exception
        return html("")  # Should be ignored

    @app.get("/empty/<fail>")
    def empty_fail(request, fail):
        if fail == "fail":
            raise Exception
        return empty()

    @app.get("/json/<fail>")
    def json_fail(request, fail):
        if fail == "fail":
            raise Exception
        # After 23.3 route format should become json, older versions think it
        # is mixed due to empty mapping to html, and don't find any format.
        return json({"foo": "bar"}) if fail == "json" else empty()

    @app.get("/html/<fail>")
    def html_fail(request, fail):
        if fail == "fail":
            raise Exception
        return html("<h1>foo</h1>")

    @app.get("/text/<fail>")
    def text_fail(request, fail):
        if fail == "fail":
            raise Exception
        return text("foo")

    @app.get("/mixed/<param>")
    def mixed_fail(request, param):
        if param not in ("json", "html"):
            raise Exception
        return json({}) if param == "json" else html("")

    return app


@pytest.fixture
def fake_request(app):
    return Request(b"/foobar", {"accept": "*/*"}, "1.1", "GET", None, app)


@pytest.mark.parametrize(
    "fallback,content_type, exception, status",
    (
        (None, "text/plain; charset=utf-8", Exception, 500),
        ("html", "text/html; charset=utf-8", Exception, 500),
        ("auto", "text/plain; charset=utf-8", Exception, 500),
        ("text", "text/plain; charset=utf-8", Exception, 500),
        ("json", "application/json", Exception, 500),
        (None, "text/plain; charset=utf-8", NotFound, 404),
        ("html", "text/html; charset=utf-8", NotFound, 404),
        ("auto", "text/plain; charset=utf-8", NotFound, 404),
        ("text", "text/plain; charset=utf-8", NotFound, 404),
        ("json", "application/json", NotFound, 404),
    ),
)
def test_should_return_html_valid_setting(
    fake_request, fallback, content_type, exception, status
):
    # Note: if fallback is None or "auto", prior to PR #2668 base was returned
    # and after that a text response is given because it matches */*. Changed
    # base to TextRenderer in this test, like it is in Sanic itself, so the
    # test passes with either version but still covers everything that it did.
    if fallback:
        fake_request.app.config.FALLBACK_ERROR_FORMAT = fallback

    try:
        raise exception("bad stuff")
    except Exception as e:
        response = exception_response(
            fake_request,
            e,
            True,
            base=TextRenderer,
            fallback=fake_request.app.config.FALLBACK_ERROR_FORMAT,
        )

    assert isinstance(response, HTTPResponse)
    assert response.status == status
    assert response.content_type == content_type


def test_auto_fallback_with_data(app):
    app.config.FALLBACK_ERROR_FORMAT = "auto"

    _, response = app.test_client.get("/error")
    assert response.status == 500
    assert response.content_type == "text/plain; charset=utf-8"

    _, response = app.test_client.post("/error", json={"foo": "bar"})
    assert response.status == 500
    assert response.content_type == "application/json"

    _, response = app.test_client.post("/error", data={"foo": "bar"})
    assert response.status == 500
    assert response.content_type == "text/plain; charset=utf-8"


def test_auto_fallback_with_content_type(app):
    app.config.FALLBACK_ERROR_FORMAT = "auto"

    _, response = app.test_client.get(
        "/error", headers={"content-type": "application/json", "accept": "*/*"}
    )
    assert response.status == 500
    assert response.content_type == "application/json"

    _, response = app.test_client.get(
        "/error", headers={"content-type": "foo/bar", "accept": "*/*"}
    )
    assert response.status == 500
    assert response.content_type == "text/plain; charset=utf-8"


def test_route_error_format_set_on_auto(app):
    @app.get("/text")
    def text_response(request):
        return text(request.route.extra.error_format)

    @app.get("/json")
    def json_response(request):
        return json({"format": request.route.extra.error_format})

    @app.get("/html")
    def html_response(request):
        return html(request.route.extra.error_format)

    _, response = app.test_client.get("/text")
    assert response.text == "text"

    _, response = app.test_client.get("/json")
    assert response.json["format"] == "json"

    _, response = app.test_client.get("/html")
    assert response.text == "html"


def test_route_error_response_from_auto_route(app):
    @app.get("/text")
    def text_response(request):
        raise Exception("oops")
        return text("Never gonna see this")

    @app.get("/json")
    def json_response(request):
        raise Exception("oops")
        return json({"message": "Never gonna see this"})

    @app.get("/html")
    def html_response(request):
        raise Exception("oops")
        return html("<h1>Never gonna see this</h1>")

    _, response = app.test_client.get("/text")
    assert response.content_type == "text/plain; charset=utf-8"

    _, response = app.test_client.get("/json")
    assert response.content_type == "application/json"

    _, response = app.test_client.get("/html")
    assert response.content_type == "text/html; charset=utf-8"


def test_route_error_response_from_explicit_format(app):
    @app.get("/text", error_format="json")
    def text_response(request):
        raise Exception("oops")
        return text("Never gonna see this")

    @app.get("/json", error_format="text")
    def json_response(request):
        raise Exception("oops")
        return json({"message": "Never gonna see this"})

    _, response = app.test_client.get("/text")
    assert response.content_type == "application/json"

    _, response = app.test_client.get("/json")
    assert response.content_type == "text/plain; charset=utf-8"


def test_unknown_fallback_format(app):
    with pytest.raises(SanicException, match="Unknown format: bad"):
        app.config.FALLBACK_ERROR_FORMAT = "bad"


def test_route_error_format_unknown(app):
    with pytest.raises(SanicException, match="Unknown format: bad"):

        @app.get("/text", error_format="bad")
        def handler(request):
            ...


def test_fallback_with_content_type_html(app):
    app.config.FALLBACK_ERROR_FORMAT = "auto"

    _, response = app.test_client.get(
        "/error",
        headers={"content-type": "application/json", "accept": "text/html"},
    )
    assert response.status == 500
    assert response.content_type == "text/html; charset=utf-8"


def test_fallback_with_content_type_mismatch_accept(app):
    app.config.FALLBACK_ERROR_FORMAT = "auto"

    _, response = app.test_client.get(
        "/error",
        headers={"content-type": "application/json", "accept": "text/plain"},
    )
    assert response.status == 500
    assert response.content_type == "text/plain; charset=utf-8"

    _, response = app.test_client.get(
        "/error",
        headers={"content-type": "text/html", "accept": "foo/bar"},
    )
    assert response.status == 500
    assert response.content_type == "text/plain; charset=utf-8"

    app.router.reset()

    @app.route("/alt1")
    @app.route("/alt2", error_format="text")
    @app.route("/alt3", error_format="html")
    def handler(_):
        raise Exception("problem here")
        # Yes, we know this return value is unreachable. This is on purpose.
        return json({})

    app.router.finalize()

    _, response = app.test_client.get(
        "/alt1",
        headers={"accept": "foo/bar"},
    )
    assert response.status == 500
    assert response.content_type == "text/plain; charset=utf-8"
    _, response = app.test_client.get(
        "/alt1",
        headers={"accept": "foo/bar,*/*"},
    )
    assert response.status == 500
    assert response.content_type == "application/json"

    _, response = app.test_client.get(
        "/alt2",
        headers={"accept": "foo/bar"},
    )
    assert response.status == 500
    assert response.content_type == "text/plain; charset=utf-8"
    _, response = app.test_client.get(
        "/alt2",
        headers={"accept": "foo/bar,*/*"},
    )
    assert response.status == 500
    assert response.content_type == "text/plain; charset=utf-8"

    _, response = app.test_client.get(
        "/alt3",
        headers={"accept": "foo/bar"},
    )
    assert response.status == 500
    assert response.content_type == "text/plain; charset=utf-8"

    _, response = app.test_client.get(
        "/alt3",
        headers={"accept": "foo/bar,text/html"},
    )
    assert response.status == 500
    assert response.content_type == "text/html; charset=utf-8"


@pytest.mark.parametrize(
    "accept,content_type,expected",
    (
        (None, None, "text/plain; charset=utf-8"),
        ("foo/bar", None, "text/plain; charset=utf-8"),
        ("application/json", None, "application/json"),
        ("application/json,text/plain", None, "application/json"),
        ("text/plain,application/json", None, "application/json"),
        ("text/plain,foo/bar", None, "text/plain; charset=utf-8"),
        ("text/plain,text/html", None, "text/plain; charset=utf-8"),
        ("*/*", "foo/bar", "text/plain; charset=utf-8"),
        ("*/*", "application/json", "application/json"),
        # App wants text/plain but accept has equal entries for it
        ("text/*,*/plain", None, "text/plain; charset=utf-8"),
    ),
)
def test_combinations_for_auto(fake_request, accept, content_type, expected):
    if accept:
        fake_request.headers["accept"] = accept
    else:
        del fake_request.headers["accept"]

    if content_type:
        fake_request.headers["content-type"] = content_type

    try:
        raise Exception("bad stuff")
    except Exception as e:
        response = exception_response(
            fake_request,
            e,
            True,
            base=TextRenderer,
            fallback="auto",
        )

    assert response.content_type == expected


def test_allow_fallback_error_format_set_main_process_start(app):
    @app.main_process_start
    async def start(app, _):
        app.config.FALLBACK_ERROR_FORMAT = "text"

    _, response = app.test_client.get("/error")
    assert response.status == 500
    assert response.content_type == "text/plain; charset=utf-8"


def test_setting_fallback_on_config_changes_as_expected(app):
    app.error_handler = ErrorHandler()

    _, response = app.test_client.get("/error")
    assert response.content_type == "text/plain; charset=utf-8"

    app.config.FALLBACK_ERROR_FORMAT = "html"
    _, response = app.test_client.get("/error")
    assert response.content_type == "text/html; charset=utf-8"

    app.config.FALLBACK_ERROR_FORMAT = "text"
    _, response = app.test_client.get("/error")
    assert response.content_type == "text/plain; charset=utf-8"


def test_allow_fallback_error_format_in_config_injection():
    class MyConfig(Config):
        FALLBACK_ERROR_FORMAT = "text"

    app = Sanic("test", config=MyConfig())

    @app.route("/error", methods=["GET", "POST"])
    def err(request):
        raise Exception("something went wrong")

    request, response = app.test_client.get("/error")
    assert response.status == 500
    assert response.content_type == "text/plain; charset=utf-8"


def test_allow_fallback_error_format_in_config_replacement(app):
    class MyConfig(Config):
        FALLBACK_ERROR_FORMAT = "text"

    app.config = MyConfig()

    request, response = app.test_client.get("/error")
    assert response.status == 500
    assert response.content_type == "text/plain; charset=utf-8"


def test_config_fallback_before_and_after_startup(app):
    app.config.FALLBACK_ERROR_FORMAT = "json"

    @app.main_process_start
    async def start(app, _):
        app.config.FALLBACK_ERROR_FORMAT = "text"

    _, response = app.test_client.get("/error")
    assert response.status == 500
    assert response.content_type == "application/json"


def test_config_fallback_using_update_dict(app):
    app.config.update({"FALLBACK_ERROR_FORMAT": "text"})

    _, response = app.test_client.get("/error")
    assert response.status == 500
    assert response.content_type == "text/plain; charset=utf-8"


def test_config_fallback_using_update_kwarg(app):
    app.config.update(FALLBACK_ERROR_FORMAT="text")

    _, response = app.test_client.get("/error")
    assert response.status == 500
    assert response.content_type == "text/plain; charset=utf-8"


def test_config_fallback_bad_value(app):
    message = "Unknown format: fake"
    with pytest.raises(SanicException, match=message):
        app.config.FALLBACK_ERROR_FORMAT = "fake"


@pytest.mark.parametrize(
    "route_format,fallback,accept,expected",
    (
        (
            "json",
            "html",
            "*/*",
            "The client accepts */*, using 'json' from fakeroute",
        ),
        (
            "json",
            "auto",
            "text/html,*/*;q=0.8",
            "The client accepts text/html, using 'html' from any",
        ),
        (
            "json",
            "json",
            "text/html,*/*;q=0.8",
            "The client accepts */*;q=0.8, using 'json' from fakeroute",
        ),
        (
            "",
            "html",
            "text/*,*/plain",
            "The client accepts text/*, using 'html' from FALLBACK_ERROR_FORMAT",
        ),
        (
            "",
            "json",
            "text/*,*/*",
            "The client accepts */*, using 'json' from FALLBACK_ERROR_FORMAT",
        ),
        (
            "",
            "auto",
            "*/*,application/json;q=0.5",
            "The client accepts */*, using 'json' from request.accept",
        ),
        (
            "",
            "auto",
            "*/*",
            "The client accepts */*, using 'json' from content-type",
        ),
        (
            "",
            "auto",
            "text/html,text/plain",
            "The client accepts text/plain, using 'text' from any",
        ),
        (
            "",
            "auto",
            "text/html,text/plain;q=0.9",
            "The client accepts text/html, using 'html' from any",
        ),
        (
            "html",
            "json",
            "application/xml",
            "No format found, the client accepts [application/xml]",
        ),
        ("", "auto", "*/*", "The client accepts */*, using 'text' from any"),
        ("", "", "*/*", "No format found, the client accepts [*/*]"),
        # DEPRECATED: remove in 24.3
        (
            "",
            "auto",
            "*/*",
            "The client accepts */*, using 'json' from request.json",
        ),
    ),
)
def test_guess_mime_logging(
    caplog, fake_request, route_format, fallback, accept, expected
):
    class FakeObject:
        pass

    fake_request.route = FakeObject()
    fake_request.route.name = "fakeroute"
    fake_request.route.extra = FakeObject()
    fake_request.route.extra.error_format = route_format
    if accept is None:
        del fake_request.headers["accept"]
    else:
        fake_request.headers["accept"] = accept

    if "content-type" in expected:
        fake_request.headers["content-type"] = "application/json"

    # Fake JSON content (DEPRECATED: remove in 24.3)
    if "request.json" in expected:
        fake_request.parsed_json = {"foo": "bar"}

    with caplog.at_level(logging.DEBUG, logger="sanic.root"):
        guess_mime(fake_request, fallback)

    (logmsg,) = [
        r.message for r in caplog.records if r.funcName == "guess_mime"
    ]

    assert logmsg == expected
