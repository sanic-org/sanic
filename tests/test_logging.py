import logging
import os
import sys
import uuid

from importlib import reload
from io import StringIO

import pytest

from sanic_testing.testing import SanicTestClient

import sanic

from sanic import Sanic
from sanic.compat import OS_IS_WINDOWS
from sanic.log import LOGGING_CONFIG_DEFAULTS, logger
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


def test_logging_defaults():
    # reset_logging()
    app = Sanic("test_logging")

    for fmt in [h.formatter for h in logging.getLogger("sanic.root").handlers]:
        assert (
            fmt._fmt
            == LOGGING_CONFIG_DEFAULTS["formatters"]["generic"]["format"]
        )

    for fmt in [
        h.formatter for h in logging.getLogger("sanic.error").handlers
    ]:
        assert (
            fmt._fmt
            == LOGGING_CONFIG_DEFAULTS["formatters"]["generic"]["format"]
        )

    for fmt in [
        h.formatter for h in logging.getLogger("sanic.access").handlers
    ]:
        assert (
            fmt._fmt
            == LOGGING_CONFIG_DEFAULTS["formatters"]["access"]["format"]
        )


def test_logging_pass_customer_logconfig():
    # reset_logging()

    modified_config = LOGGING_CONFIG_DEFAULTS
    modified_config["formatters"]["generic"][
        "format"
    ] = "%(asctime)s - (%(name)s)[%(levelname)s]: %(message)s"
    modified_config["formatters"]["access"][
        "format"
    ] = "%(asctime)s - (%(name)s)[%(levelname)s]: %(message)s"

    app = Sanic("test_logging", log_config=modified_config)

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


@pytest.mark.parametrize(
    "debug",
    (
        True,
        False,
    ),
)
def test_log_connection_lost(app, debug, monkeypatch):
    """ Should not log Connection lost exception on non debug """
    stream = StringIO()
    root = logging.getLogger("sanic.root")
    root.addHandler(logging.StreamHandler(stream))
    monkeypatch.setattr(sanic.server, "logger", root)

    @app.route("/conn_lost")
    async def conn_lost(request):
        response = text("Ok")
        request.transport.close()
        return response

    req, res = app.test_client.get("/conn_lost", debug=debug, allow_none=True)
    assert res is None

    log = stream.getvalue()

    if debug:
        assert "Connection lost before response written @" in log
    else:
        assert "Connection lost before response written @" not in log


@pytest.mark.asyncio
async def test_logger(caplog):
    rand_string = str(uuid.uuid4())

    app = Sanic(name=__name__)

    @app.get("/")
    def log_info(request):
        logger.info(rand_string)
        return text("hello")

    with caplog.at_level(logging.INFO):
        _ = await app.asgi_client.get("/")

    record = ("sanic.root", logging.INFO, rand_string)
    assert record in caplog.record_tuples


@pytest.mark.skipif(
    OS_IS_WINDOWS and sys.version_info >= (3, 8),
    reason="Not testable with current client",
)
def test_logger_static_and_secure(caplog):
    # Same as test_logger, except for more coverage:
    # - test_client initialised separately for static port
    # - using ssl
    rand_string = str(uuid.uuid4())

    app = Sanic(name=__name__)

    @app.get("/")
    def log_info(request):
        logger.info(rand_string)
        return text("hello")

    current_dir = os.path.dirname(os.path.realpath(__file__))
    ssl_cert = os.path.join(current_dir, "certs/selfsigned.cert")
    ssl_key = os.path.join(current_dir, "certs/selfsigned.key")

    ssl_dict = {"cert": ssl_cert, "key": ssl_key}

    test_client = SanicTestClient(app, port=42101)
    with caplog.at_level(logging.INFO):
        request, response = test_client.get(
            f"https://127.0.0.1:{test_client.port}/",
            server_kwargs=dict(ssl=ssl_dict),
        )

    port = test_client.port

    assert caplog.record_tuples[0] == (
        "sanic.root",
        logging.INFO,
        f"Goin' Fast @ https://127.0.0.1:{port}",
    )
    assert caplog.record_tuples[1] == (
        "sanic.root",
        logging.INFO,
        f"https://127.0.0.1:{port}/",
    )
    assert caplog.record_tuples[2] == ("sanic.root", logging.INFO, rand_string)
    assert caplog.record_tuples[-1] == (
        "sanic.root",
        logging.INFO,
        "Server Stopped",
    )


def test_logging_modified_root_logger_config():
    # reset_logging()

    modified_config = LOGGING_CONFIG_DEFAULTS
    modified_config["loggers"]["sanic.root"]["level"] = "DEBUG"

    app = Sanic("test_logging", log_config=modified_config)

    assert logging.getLogger("sanic.root").getEffectiveLevel() == logging.DEBUG
