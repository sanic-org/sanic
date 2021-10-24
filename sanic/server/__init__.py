import asyncio
import os

from distutils.util import strtobool

from sanic.compat import OS_IS_WINDOWS
from sanic.log import error_logger
from sanic.models.server_types import ConnInfo, Signal
from sanic.server.async_server import AsyncioServer
from sanic.server.protocols.http_protocol import HttpProtocol
from sanic.server.runners import serve, serve_multiple, serve_single


def use_uvloop() -> None:
    """
    Use uvloop instead of the default asyncio loop.
    """
    try:
        import uvloop  # type: ignore
        if strtobool(os.environ.get("SANIC_NO_UVLOOP", "no")):
            error_logger.warning(
                "You are running Sanic using uvloop, but the "
                "'SANIC_NO_UVLOOP' environment variable (used to opt-out "
                "of installing uvloop with Sanic) is set to true. If you "
                "want to disable uvloop with Sanic, set the 'USE_UVLOOP' "
                "configuration value to false."
            )

        if not isinstance(
            asyncio.get_event_loop_policy(), uvloop.EventLoopPolicy
        ):
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    except ImportError:
        if not OS_IS_WINDOWS:
            error_logger.warning(
                "You are trying to use uvloop, but uvloop is not "
                "installed in your system. In order to use uvloop "
                "you must first install it. Otherwise, you can disable "
                "uvloop completely by setting the 'USE_UVLOOP' "
                "configuration value to false. Sanic will now continue "
                "to run without using uvloop."
            )


__all__ = (
    "AsyncioServer",
    "ConnInfo",
    "HttpProtocol",
    "Signal",
    "serve",
    "serve_multiple",
    "serve_single",
)
