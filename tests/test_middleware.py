import logging

from asyncio import CancelledError
from itertools import count

from sanic.exceptions import NotFound, SanicException
from sanic.request import Request
from sanic.response import HTTPResponse, text


# ------------------------------------------------------------ #
#  GET
# ------------------------------------------------------------ #


def test_middleware_request(app):
    results = []

    @app.middleware
    async def handler1(request):
        results.append(request)

    @app.route("/")
    async def handler2(request):
        return text("OK")

    request, response = app.test_client.get("/")

    assert response.text == "OK"
    assert type(results[0]) is Request


def test_middleware_request_as_convenience(app):
    results = []

    @app.on_request
    async def handler1(request):
        results.append(request)

    @app.route("/")
    async def handler2(request):
        return text("OK")

    request, response = app.test_client.get("/")

    assert response.text == "OK"
    assert type(results[0]) is Request


def test_middleware_response(app):
    results = []

    @app.middleware("request")
    async def process_request(request):
        results.append(request)

    @app.middleware("response")
    async def process_response(request, response):
        results.append(request)
        results.append(response)

    @app.route("/")
    async def handler(request):
        return text("OK")

    request, response = app.test_client.get("/")

    assert response.text == "OK"
    assert type(results[0]) is Request
    assert type(results[1]) is Request
    assert isinstance(results[2], HTTPResponse)


def test_middleware_response_as_convenience(app):
    results = []

    @app.on_request
    async def process_request(request):
        results.append(request)

    @app.on_response
    async def process_response(request, response):
        results.append(request)
        results.append(response)

    @app.route("/")
    async def handler(request):
        return text("OK")

    request, response = app.test_client.get("/")

    assert response.text == "OK"
    assert type(results[0]) is Request
    assert type(results[1]) is Request
    assert isinstance(results[2], HTTPResponse)


def test_middleware_response_as_convenience_called(app):
    results = []

    @app.on_request()
    async def process_request(request):
        results.append(request)

    @app.on_response()
    async def process_response(request, response):
        results.append(request)
        results.append(response)

    @app.route("/")
    async def handler(request):
        return text("OK")

    request, response = app.test_client.get("/")

    assert response.text == "OK"
    assert type(results[0]) is Request
    assert type(results[1]) is Request
    assert isinstance(results[2], HTTPResponse)


def test_middleware_response_exception(app):
    result = {"status_code": "middleware not run"}

    @app.middleware("response")
    async def process_response(request, response):
        result["status_code"] = response.status
        return response

    @app.exception(NotFound)
    async def error_handler(request, exception):
        return text("OK", exception.status_code)

    @app.route("/")
    async def handler(request):
        return text("FAIL")

    request, response = app.test_client.get("/page_not_found")
    assert response.text == "OK"
    assert result["status_code"] == 404


def test_middleware_response_raise_cancelled_error(app, caplog):
    app.config.RESPONSE_TIMEOUT = 1

    @app.middleware("response")
    async def process_response(request, response):
        raise CancelledError("CancelledError at response middleware")

    @app.get("/")
    def handler(request):
        return text("OK")

    with caplog.at_level(logging.ERROR):
        reqrequest, response = app.test_client.get("/")

        assert response.status == 503
        assert (
            "sanic.root",
            logging.ERROR,
            "Exception occurred while handling uri: 'http://127.0.0.1:42101/'",
        ) not in caplog.record_tuples


def test_middleware_response_raise_exception(app, caplog):
    @app.middleware("response")
    async def process_response(request, response):
        raise Exception("Exception at response middleware")

    app.route("/")(lambda x: x)
    with caplog.at_level(logging.ERROR):
        reqrequest, response = app.test_client.get("/fail")

    assert response.status == 404
    # 404 errors are not logged
    assert (
        "sanic.root",
        logging.ERROR,
        "Exception occurred while handling uri: 'http://127.0.0.1:42101/'",
    ) not in caplog.record_tuples
    # Middleware exception ignored but logged
    assert (
        "sanic.error",
        logging.ERROR,
        "Exception occurred in one of response middleware handlers",
    ) in caplog.record_tuples


def test_middleware_override_request(app):
    @app.middleware
    async def halt_request(request):
        return text("OK")

    @app.route("/")
    async def handler(request):
        return text("FAIL")

    _, response = app.test_client.get("/", gather_request=False)

    assert response.status == 200
    assert response.text == "OK"


def test_middleware_override_response(app):
    @app.middleware("response")
    async def process_response(request, response):
        return text("OK")

    @app.route("/")
    async def handler(request):
        return text("FAIL")

    request, response = app.test_client.get("/")

    assert response.status == 200
    assert response.text == "OK"


def test_middleware_order(app):
    order = []

    @app.middleware("request")
    async def request1(request):
        order.append(1)

    @app.middleware("request")
    async def request2(request):
        order.append(2)

    @app.middleware("request")
    async def request3(request):
        order.append(3)

    @app.middleware("response")
    async def response1(request, response):
        order.append(6)

    @app.middleware("response")
    async def response2(request, response):
        order.append(5)

    @app.middleware("response")
    async def response3(request, response):
        order.append(4)

    @app.route("/")
    async def handler(request):
        return text("OK")

    request, response = app.test_client.get("/")

    assert response.status == 200
    assert order == [1, 2, 3, 4, 5, 6]


def test_request_middleware_executes_once(app):
    i = count()

    @app.middleware("request")
    async def inc(request):
        nonlocal i
        next(i)

    @app.route("/")
    async def handler(request):
        await request.app._run_request_middleware(request)
        return text("OK")

    request, response = app.test_client.get("/")
    assert next(i) == 1

    request, response = app.test_client.get("/")
    assert next(i) == 3
