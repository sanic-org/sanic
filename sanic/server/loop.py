import asyncio
import sys

from os import getenv

from sanic.compat import OS_IS_WINDOWS
from sanic.log import error_logger
from sanic.utils import str_to_bool


def try_use_uvloop() -> None:
    """
    Use uvloop instead of the default asyncio loop.
    """
    if OS_IS_WINDOWS:
        error_logger.warning(
            "You are trying to use uvloop, but uvloop is not compatible "
            "with your system. You can disable uvloop completely by setting "
            "the 'USE_UVLOOP' configuration value to false, or simply not "
            "defining it and letting Sanic handle it for you. Sanic will now "
            "continue to run using the default event loop."
        )
        return

    try:
        import uvloop  # type: ignore
    except ImportError:
        error_logger.warning(
            "You are trying to use uvloop, but uvloop is not "
            "installed in your system. In order to use uvloop "
            "you must first install it. Otherwise, you can disable "
            "uvloop completely by setting the 'USE_UVLOOP' "
            "configuration value to false. Sanic will now continue "
            "to run with the default event loop."
        )
        return

    uvloop_install_removed = str_to_bool(getenv("SANIC_NO_UVLOOP", "no"))
    if uvloop_install_removed:
        error_logger.info(
            "You are requesting to run Sanic using uvloop, but the "
            "install-time 'SANIC_NO_UVLOOP' environment variable (used to "
            "opt-out of installing uvloop with Sanic) is set to true. If "
            "you want to prevent Sanic from overriding the event loop policy "
            "during runtime, set the 'USE_UVLOOP' configuration value to "
            "false."
        )

    if not isinstance(asyncio.get_event_loop_policy(), uvloop.EventLoopPolicy):
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def try_windows_loop():
    if not OS_IS_WINDOWS:
        error_logger.warning(
            "You are trying to use an event loop policy that is not "
            "compatible with your system. You can simply let Sanic handle "
            "selecting the best loop for you. Sanic will now continue to run "
            "using the default event loop."
        )
        return

    if sys.version_info >= (3, 8) and not isinstance(
        asyncio.get_event_loop_policy(), asyncio.WindowsSelectorEventLoopPolicy
    ):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
