import errno
import sys

from typing import Callable

from sanic.exceptions import ServerError
from sanic.log import error_logger
from sanic.worker.daemon import DaemonError


ExceptionHandler = Callable[[Exception], bool]


def maybe_handle_startup_error(exc: Exception) -> None:
    for handler in EXCEPTION_HANDLERS:
        if handler(exc):
            sys.exit(1)
    raise exc


def _handle_os_error(exc: Exception) -> bool:
    if not isinstance(exc, OSError):
        return False

    if exc.errno == errno.EADDRINUSE:
        error_logger.error(
            "Startup failed: Address already in use. \n\n"
            "Ensure no other process is using the same address and port, "
            "or configure the server to use a different port."
        )
    else:
        error_logger.error(
            "Startup failed due to OS error: %s (errno %s)",
            exc.strerror,
            exc.errno,
        )
    return True


def _handle_server_error(exc: Exception) -> bool:
    if not isinstance(exc, ServerError):
        return False

    error_logger.error(f"Startup failed due to server error. {exc}")
    return True


def _handle_daemon_error(exc: Exception) -> bool:
    if not isinstance(exc, DaemonError):
        return False

    error_logger.error(f"Daemon error: {exc}")
    return True


EXCEPTION_HANDLERS: tuple[ExceptionHandler, ...] = (
    _handle_os_error,
    _handle_server_error,
    _handle_daemon_error,
)
