from bs4 import BeautifulSoup

from sanic import Sanic
from sanic.exceptions import InvalidUsage, NotFound, ServerError
from sanic.handlers import ErrorHandler
from sanic.response import text


exception_handler_app = Sanic("test_exception_handler")


@exception_handler_app.route("/1")
def handler_1(request):
    raise InvalidUsage("OK")


@exception_handler_app.route("/2")
def handler_2(request):
    raise ServerError("OK")


@exception_handler_app.route("/3")
def handler_3(request):
    raise NotFound("OK")


@exception_handler_app.route("/4")
def handler_4(request):
    foo = bar  # noqa -- F821 undefined name 'bar' is done to throw exception
    return text(foo)


@exception_handler_app.route("/5")
def handler_5(request):
    class CustomServerError(ServerError):
        pass

    raise CustomServerError("Custom server error")


@exception_handler_app.route("/6/<arg:int>")
def handler_6(request, arg):
    try:
        foo = 1 / arg
    except Exception as e:
        raise e from ValueError(f"{arg}")
    return text(foo)


@exception_handler_app.exception(NotFound, ServerError)
def handler_exception(request, exception):
    return text("OK")


def test_invalid_usage_exception_handler():
    request, response = exception_handler_app.test_client.get("/1")
    assert response.status == 400


def test_server_error_exception_handler():
    request, response = exception_handler_app.test_client.get("/2")
    assert response.status == 200
    assert response.text == "OK"


def test_not_found_exception_handler():
    request, response = exception_handler_app.test_client.get("/3")
    assert response.status == 200


def test_text_exception__handler():
    request, response = exception_handler_app.test_client.get("/random")
    assert response.status == 200
    assert response.text == "OK"


def test_html_traceback_output_in_debug_mode():
    request, response = exception_handler_app.test_client.get("/4", debug=True)
    assert response.status == 500
    soup = BeautifulSoup(response.body, "html.parser")
    html = str(soup)

    assert "response = handler(request, *args, **kwargs)" in html
    assert "handler_4" in html
    assert "foo = bar" in html

    summary_text = " ".join(soup.select(".summary")[0].text.split())
    assert (
        "NameError: name 'bar' is not defined while handling path /4"
    ) == summary_text


def test_inherited_exception_handler():
    request, response = exception_handler_app.test_client.get("/5")
    assert response.status == 200


def test_chained_exception_handler():
    request, response = exception_handler_app.test_client.get(
        "/6/0", debug=True
    )
    assert response.status == 500

    soup = BeautifulSoup(response.body, "html.parser")
    html = str(soup)

    assert "response = handler(request, *args, **kwargs)" in html
    assert "handler_6" in html
    assert "foo = 1 / arg" in html
    assert "ValueError" in html
    assert "The above exception was the direct cause" in html

    summary_text = " ".join(soup.select(".summary")[0].text.split())
    assert (
        "ZeroDivisionError: division by zero while handling path /6/0"
    ) == summary_text


def test_exception_handler_lookup():
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

    assert handler.lookup(ImportError()) == import_error_handler
    assert handler.lookup(ModuleNotFoundError()) == import_error_handler
    assert handler.lookup(CustomError()) == custom_error_handler
    assert handler.lookup(ServerError("Error")) == server_error_handler
    assert handler.lookup(CustomServerError("Error")) == server_error_handler

    # once again to ensure there is no caching bug
    assert handler.lookup(ImportError()) == import_error_handler
    assert handler.lookup(ModuleNotFoundError()) == import_error_handler
    assert handler.lookup(CustomError()) == custom_error_handler
    assert handler.lookup(ServerError("Error")) == server_error_handler
    assert handler.lookup(CustomServerError("Error")) == server_error_handler
