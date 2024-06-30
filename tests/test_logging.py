import logging
import sys
import uuid

from importlib import reload
from io import StringIO
from unittest.mock import ANY, Mock

import pytest

import sanic

from sanic import Sanic
from sanic.log import LOGGING_CONFIG_DEFAULTS, Colors, logger
from sanic.logging.formatter import (
    AutoFormatter,
    DebugAccessFormatter,
    DebugFormatter,
    ProdAccessFormatter,
    ProdFormatter,
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
    AutoFormatter.ATTY = False
    AutoFormatter.SETUP = False
    Sanic("test_logging")
    setup_logging(debug)
    std_formatter = (DebugFormatter if debug else ProdFormatter)()
    access_formatter = (
        DebugAccessFormatter if debug else ProdAccessFormatter
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


@pytest.mark.parametrize(
    "atty,no_color,expected",
    [
        (True, False, True),
        (False, False, False),
        (True, True, False),
        (False, True, False),
    ],
)
@pytest.mark.xfail(reason="Runs on local but fails on CI, not highly critical")
def test_debug_formatter_formatException(atty, no_color, expected):
    formatter = DebugFormatter()
    formatter.ATTY = atty
    formatter.NO_COLOR = no_color

    try:
        1 / 0
    except Exception as e:
        exc_info = (type(e), e, e.__traceback__)

    output = formatter.formatException(exc_info)
    lines = output.splitlines()

    assert len(lines) == 5 if sys.version_info >= (3, 11) else 4
    assert ("\033" in output) is expected
    assert ("\033[36m\033[1m" in lines[1]) is expected
    assert (
        lines[1].endswith(
            "\033[34m\033[1mtest_debug_formatter_formatException\033[0m"
        )
        is expected
    )
    assert (
        lines[1].endswith("test_debug_formatter_formatException")
        is not expected
    )
    assert (lines[2] == "\033[33m    1 / 0\033[0m") is expected
    assert (lines[2] == "    1 / 0") is not expected
    assert (
        lines[-1] == "\033[38;2;255;13;104m\033[1mZeroDivisionError\033[0m: "
        "\033[1mdivision by zero\033[0m"
    ) is expected
    assert (lines[-1] == "ZeroDivisionError: division by zero") is not expected
