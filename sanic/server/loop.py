import asyncio

from collections.abc import Callable
from os import getenv

from sanic.compat import OS_IS_WINDOWS
from sanic.log import error_logger
from sanic.utils import str_to_bool


LoopFactory = Callable[[], asyncio.AbstractEventLoop]

_loop_factory: LoopFactory | None = None


def _set_loop_factory(factory: LoopFactory) -> None:
    global _loop_factory
    _loop_factory = factory


def new_event_loop() -> asyncio.AbstractEventLoop:
    """Create a new event loop.

    The loop is created by the factory registered through
    `try_use_uvloop` or `try_windows_loop` when one has been set, and
    falls back to the default asyncio event loop otherwise. Keeping the
    selection in a factory means Sanic never has to install a
    process-wide event loop policy, an API that is deprecated and
    slated for removal.

    Returns:
        AbstractEventLoop: A new event loop of the selected type.
    """
    if _loop_factory is not None:
        return _loop_factory()
    return asyncio.new_event_loop()


def try_use_uvloop() -> None:
    """Use uvloop instead of the default asyncio loop."""
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
            "you want to prevent Sanic from selecting uvloop as the loop "
            "factory during runtime, set the 'USE_UVLOOP' configuration "
            "value to false."
        )

    _set_loop_factory(uvloop.new_event_loop)


def try_windows_loop():
    """Try to use a selector event loop instead of the Windows default"""
    if not OS_IS_WINDOWS:
        error_logger.warning(
            "You are trying to use the Windows selector event loop, which "
            "is not compatible with your system. You can simply let Sanic "
            "handle selecting the best loop for you. Sanic will now "
            "continue to run using the default event loop."
        )
        return

    _set_loop_factory(asyncio.SelectorEventLoop)
