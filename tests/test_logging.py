import logging
import uuid

from importlib import reload
from io import StringIO
from unittest.mock import ANY, Mock

import pytest

import sanic

from sanic import Sanic
from sanic.log import LOGGING_CONFIG_DEFAULTS, Colors, logger
from sanic.logging.formatter import (
    SanicAutoFormatter,
    SanicDebugAccessFormatter,
    SanicDebugFormatter,
    SanicProdAccessFormatter,
    SanicProdFormatter,
)
from sanic.logging.setup import setup_logging
from sanic.response import text


logging_format = """module: %(module)s; \
function: %(funcName)s(); \
message: %(message)s"""


def reset_logging():
    logging.shutdown()
    reload(logging)


def test_log(app):
    log_stream = StringIO()
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(
        format=logging_format, level=logging.DEBUG, stream=log_stream
    )
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    log = logging.getLogger()
    rand_string = str(uuid.uuid4())

    @app.route("/")
    def handler(request):
        log.info(rand_string)
        return text("hello")

    request, response = app.test_client.get("/")
    log_text = log_stream.getvalue()
    assert rand_string in log_text


@pytest.mark.parametrize("debug", (True, False))
def test_logging_defaults(debug):
    SanicAutoFormatter.ATTY = False
    SanicAutoFormatter.SETUP = False
    Sanic("test_logging")
    setup_logging(debug)
    std_formatter = (SanicDebugFormatter if debug else SanicProdFormatter)()
    access_formatter = (
        SanicDebugAccessFormatter if debug else SanicProdAccessFormatter
    )()

    for logger_name, formatter in [
        ("sanic.root", std_formatter),
        ("sanic.error", std_formatter),
        ("sanic.access", access_formatter),
        ("sanic.server", std_formatter),
        ("sanic.websockets", std_formatter),
    ]:
        print("....", logger_name)
        for fmt in [
            h.formatter for h in logging.getLogger(logger_name).handlers
        ]:
            print(f"{logger_name} logger_formatter: ", fmt._fmt)
            print(f"{logger_name}        formatter: ", formatter._fmt)
            assert fmt._fmt == formatter._fmt


def test_logging_pass_customer_logconfig():
    # reset_logging()

    modified_config = LOGGING_CONFIG_DEFAULTS
    modified_config["formatters"]["generic"]["format"] = (
        "%(asctime)s - (%(name)s)[%(levelname)s]: %(message)s"
    )
    modified_config["formatters"]["access"]["format"] = (
        "%(asctime)s - (%(name)s)[%(levelname)s]: %(message)s"
    )

    Sanic("test_logging", log_config=modified_config)

    for fmt in [h.formatter for h in logging.getLogger("sanic.root").handlers]:
        assert fmt._fmt == modified_config["formatters"]["generic"]["format"]

    for fmt in [
        h.formatter for h in logging.getLogger("sanic.error").handlers
    ]:
        assert fmt._fmt == modified_config["formatters"]["generic"]["format"]

    for fmt in [
        h.formatter for h in logging.getLogger("sanic.access").handlers
    ]:
        assert fmt._fmt == modified_config["formatters"]["access"]["format"]


@pytest.mark.asyncio
async def test_logger(caplog):
    rand_string = str(uuid.uuid4())

    app = Sanic(name="Test")

    @app.get("/")
    def log_info(request):
        logger.info(rand_string)
        return text("hello")

    with caplog.at_level(logging.INFO):
        _ = await app.asgi_client.get("/")

    record = ("sanic.root", logging.INFO, rand_string)
    assert record in caplog.record_tuples


def test_logging_modified_root_logger_config():
    # reset_logging()

    modified_config = LOGGING_CONFIG_DEFAULTS
    modified_config["loggers"]["sanic.root"]["level"] = "DEBUG"

    Sanic("test_logging", log_config=modified_config)

    assert logging.getLogger("sanic.root").getEffectiveLevel() == logging.DEBUG


def test_access_log_client_ip_remote_addr(monkeypatch):
    access = Mock()
    monkeypatch.setattr(sanic.http.http1, "access_logger", access)

    app = Sanic("test_logging")
    app.config.ACCESS_LOG = True
    app.config.PROXIES_COUNT = 2

    @app.route("/")
    async def handler(request):
        return text(request.remote_addr)

    headers = {"X-Forwarded-For": "1.1.1.1, 2.2.2.2"}

    request, response = app.test_client.get("/", headers=headers)

    assert request.remote_addr == "1.1.1.1"
    access.info.assert_called_with(
        "",
        extra={
            "status": 200,
            "byte": len(response.content),
            "host": f"{request.remote_addr}:{request.port}",
            "request": f"GET {request.scheme}://{request.host}/",
            "duration": ANY,
        },
    )


def test_access_log_client_ip_reqip(monkeypatch):
    access = Mock()
    monkeypatch.setattr(sanic.http.http1, "access_logger", access)

    app = Sanic("test_logging")
    app.config.ACCESS_LOG = True

    @app.route("/")
    async def handler(request):
        return text(request.ip)

    request, response = app.test_client.get("/")

    access.info.assert_called_with(
        "",
        extra={
            "status": 200,
            "byte": len(response.content),
            "host": f"{request.ip}:{request.port}",
            "request": f"GET {request.scheme}://{request.host}/",
            "duration": ANY,
        },
    )


@pytest.mark.parametrize(
    "app_verbosity,log_verbosity,exists",
    (
        (0, 0, True),
        (0, 1, False),
        (0, 2, False),
        (1, 0, True),
        (1, 1, True),
        (1, 2, False),
        (2, 0, True),
        (2, 1, True),
        (2, 2, True),
    ),
)
def test_verbosity(app, caplog, app_verbosity, log_verbosity, exists):
    rand_string = str(uuid.uuid4())

    @app.get("/")
    def log_info(request):
        logger.info("DEFAULT")
        logger.info(rand_string, extra={"verbosity": log_verbosity})
        return text("hello")

    with caplog.at_level(logging.INFO):
        _ = app.test_client.get(
            "/", server_kwargs={"verbosity": app_verbosity}
        )

    record = ("sanic.root", logging.INFO, rand_string)

    if exists:
        assert record in caplog.record_tuples
    else:
        assert record not in caplog.record_tuples

    if app_verbosity == 0:
        assert ("sanic.root", logging.INFO, "DEFAULT") in caplog.record_tuples


def test_colors_enum_format():
    assert f"{Colors.END}" == Colors.END.value
    assert f"{Colors.BOLD}" == Colors.BOLD.value
    assert f"{Colors.BLUE}" == Colors.BLUE.value
    assert f"{Colors.GREEN}" == Colors.GREEN.value
    assert f"{Colors.PURPLE}" == Colors.PURPLE.value
    assert f"{Colors.RED}" == Colors.RED.value
    assert f"{Colors.SANIC}" == Colors.SANIC.value
    assert f"{Colors.YELLOW}" == Colors.YELLOW.value
