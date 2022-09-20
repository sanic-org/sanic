import asyncio
import logging

from typing import Callable, List
from unittest.mock import Mock

import pytest

from bs4 import BeautifulSoup
from pytest import LogCaptureFixture, MonkeyPatch, WarningsRecorder

from sanic import Sanic, handlers
from sanic.exceptions import BadRequest, Forbidden, NotFound, ServerError
from sanic.handlers import ErrorHandler
from sanic.request import Request
from sanic.response import text


class ErrorWithRequestCtx(ServerError):
    pass


@pytest.fixture
def exception_handler_app():
    exception_handler_app = Sanic("test_exception_handler")

    @exception_handler_app.route("/1", error_format="html")
    def handler_1(request):
        raise BadRequest("OK")

    @exception_handler_app.route("/2", error_format="html")
    def handler_2(request):
        raise ServerError("OK")

    @exception_handler_app.route("/3", error_format="html")
    def handler_3(request):
        raise NotFound("OK")

    @exception_handler_app.route("/4", error_format="html")
    def handler_4(request):
        foo = bar  # noqa -- F821
        return text(foo)

    @exception_handler_app.route("/5", error_format="html")
    def handler_5(request):
        class CustomServerError(ServerError):
            pass

        raise CustomServerError("Custom server error")

    @exception_handler_app.route("/6/<arg:int>", error_format="html")
    def handler_6(request, arg):
        try:
            foo = 1 / arg
        except Exception as e:
            raise e from ValueError(f"{arg}")
        return text(foo)

    @exception_handler_app.route("/7", error_format="html")
    def handler_7(request):
        raise Forbidden("go away!")

    @exception_handler_app.route("/8", error_format="html")
    def handler_8(request):

        raise ErrorWithRequestCtx("OK")

    @exception_handler_app.exception(ErrorWithRequestCtx, NotFound)
    def handler_exception_with_ctx(request, exception):
        return text(request.ctx.middleware_ran)

    @exception_handler_app.exception(ServerError)
    def handler_exception(request, exception):
        return text("OK")

    @exception_handler_app.exception(Forbidden)
    async def async_handler_exception(request, exception):
        response = await request.respond(content_type="text/csv")
        await response.send("foo,")
        await asyncio.sleep(0.001)
        await response.send("bar")

    @exception_handler_app.middleware
    async def some_request_middleware(request):
        request.ctx.middleware_ran = "Done."

    return exception_handler_app


def test_invalid_usage_exception_handler(exception_handler_app: Sanic):
    request, response = exception_handler_app.test_client.get("/1")
    assert response.status == 400


def test_server_error_exception_handler(exception_handler_app: Sanic):
    request, response = exception_handler_app.test_client.get("/2")
    assert response.status == 200
    assert response.text == "OK"


def test_not_found_exception_handler(exception_handler_app: Sanic):
    request, response = exception_handler_app.test_client.get("/3")
    assert response.status == 200


def test_text_exception__handler(exception_handler_app: Sanic):
    request, response = exception_handler_app.test_client.get("/random")
    assert response.status == 200
    assert response.text == "Done."


def test_async_exception_handler(exception_handler_app: Sanic):
    request, response = exception_handler_app.test_client.get("/7")
    assert response.status == 200
    assert response.text == "foo,bar"


def test_html_traceback_output_in_debug_mode(exception_handler_app: Sanic):
    request, response = exception_handler_app.test_client.get("/4", debug=True)
    assert response.status == 500
    soup = BeautifulSoup(response.body, "html.parser")
    html = str(soup)

    assert "handler_4" in html
    assert "foo = bar" in html

    summary_text = " ".join(soup.select(".summary")[0].text.split())
    assert (
        "NameError: name 'bar' is not defined while handling path /4"
    ) == summary_text


def test_inherited_exception_handler(exception_handler_app: Sanic):
    request, response = exception_handler_app.test_client.get("/5")
    assert response.status == 200


def test_chained_exception_handler(exception_handler_app: Sanic):
    request, response = exception_handler_app.test_client.get(
        "/6/0", debug=True
    )
    assert response.status == 500

    soup = BeautifulSoup(response.body, "html.parser")
    html = str(soup)

    assert "handler_6" in html
    assert "foo = 1 / arg" in html
    assert "ValueError" in html

    summary_text = " ".join(soup.select(".summary")[0].text.split())
    assert (
        "ZeroDivisionError: division by zero while handling path /6/0"
    ) == summary_text


def test_exception_handler_lookup(exception_handler_app: Sanic):
    class CustomError(Exception):
        pass

    class CustomServerError(ServerError):
        pass

    def custom_error_handler():
        pass

    def server_error_handler():
        pass

    def import_error_handler():
        pass

    try:
        ModuleNotFoundError
    except Exception:

        class ModuleNotFoundError(ImportError):
            pass

    handler = ErrorHandler()
    handler.add(ImportError, import_error_handler)
    handler.add(CustomError, custom_error_handler)
    handler.add(ServerError, server_error_handler)

    assert handler.lookup(ImportError(), None) == import_error_handler
    assert handler.lookup(ModuleNotFoundError(), None) == import_error_handler
    assert handler.lookup(CustomError(), None) == custom_error_handler
    assert handler.lookup(ServerError("Error"), None) == server_error_handler
    assert (
        handler.lookup(CustomServerError("Error"), None)
        == server_error_handler
    )

    # once again to ensure there is no caching bug
    assert handler.lookup(ImportError(), None) == import_error_handler
    assert handler.lookup(ModuleNotFoundError(), None) == import_error_handler
    assert handler.lookup(CustomError(), None) == custom_error_handler
    assert handler.lookup(ServerError("Error"), None) == server_error_handler
    assert (
        handler.lookup(CustomServerError("Error"), None)
        == server_error_handler
    )


def test_exception_handler_processed_request_middleware(
    exception_handler_app: Sanic,
):
    request, response = exception_handler_app.test_client.get("/8")
    assert response.status == 200
    assert response.text == "Done."


def test_error_handler_noisy_log(
    exception_handler_app: Sanic, monkeypatch: MonkeyPatch
):
    err_logger = Mock()
    monkeypatch.setattr(handlers, "error_logger", err_logger)

    exception_handler_app.config["NOISY_EXCEPTIONS"] = False
    exception_handler_app.test_client.get("/1")
    err_logger.exception.assert_not_called()

    exception_handler_app.config["NOISY_EXCEPTIONS"] = True
    request, _ = exception_handler_app.test_client.get("/1")
    err_logger.exception.assert_called_with(
        "Exception occurred while handling uri: %s", repr(request.url)
    )


def test_exception_handler_response_was_sent(
    app: Sanic,
    caplog: LogCaptureFixture,
    message_in_records: Callable[[List[logging.LogRecord], str], bool],
):
    exception_handler_ran = False

    @app.exception(ServerError)
    async def exception_handler(request, exception):
        nonlocal exception_handler_ran
        exception_handler_ran = True
        return text("Error")

    @app.route("/1")
    async def handler1(request: Request):
        response = await request.respond()
        await response.send("some text")
        raise ServerError("Exception")

    @app.route("/2")
    async def handler2(request: Request):
        await request.respond()
        raise ServerError("Exception")

    with caplog.at_level(logging.WARNING):
        _, response = app.test_client.get("/1")
        assert "some text" in response.text

    message_in_records(
        caplog.records,
        (
            "An error occurred while handling the request after at "
            "least some part of the response was sent to the client. "
            "Therefore, the response from your custom exception "
        ),
    )

    _, response = app.test_client.get("/2")
    assert "Error" in response.text


def test_warn_on_duplicate(
    app: Sanic, caplog: LogCaptureFixture, recwarn: WarningsRecorder
):
    @app.exception(ServerError)
    async def exception_handler_1(request, exception):
        ...

    @app.exception(ServerError)
    async def exception_handler_2(request, exception):
        ...

    assert len(caplog.records) == 1
    assert len(recwarn) == 1
    assert caplog.records[0].message == (
        "Duplicate exception handler definition on: route=__ALL_ROUTES__ and "
        "exception=<class 'sanic.exceptions.ServerError'>"
    )
