import logging
import sys

from enum import Enum
from typing import TYPE_CHECKING, Any, Dict
from warnings import warn

from sanic.helpers import is_atty


# Python 3.11 changed the way Enum formatting works for mixed-in types.
if sys.version_info < (3, 11, 0):

    class StrEnum(str, Enum):
        pass

else:
    if not TYPE_CHECKING:
        from enum import StrEnum


class Colors(StrEnum):  # no cov
    END = "\033[0m"
    BOLD = "\033[1m"
    BLUE = "\033[34m"
    GREEN = "\033[32m"
    PURPLE = "\033[35m"
    RED = "\033[31m"
    SANIC = "\033[38;2;255;13;104m"
    YELLOW = "\033[01;33m"
    GREY = "\033[1;30m"


LOGGING_CONFIG_DEFAULTS: Dict[str, Any] = dict(  # no cov
    version=1,
    disable_existing_loggers=False,
    loggers={
        "sanic.root": {"level": "INFO", "handlers": ["console"]},
        "sanic.error": {
            "level": "INFO",
            "handlers": ["error_console"],
            "propagate": True,
            "qualname": "sanic.error",
        },
        "sanic.access": {
            "level": "INFO",
            "handlers": ["access_console"],
            "propagate": True,
            "qualname": "sanic.access",
        },
        "sanic.server": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": True,
            "qualname": "sanic.server",
        },
    },
    handlers={
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "generic",
            "stream": sys.stdout,
        },
        "error_console": {
            "class": "logging.StreamHandler",
            "formatter": "generic",
            "stream": sys.stderr,
        },
        "access_console": {
            "class": "logging.StreamHandler",
            "formatter": "access",
            "stream": sys.stdout,
        },
    },
    formatters={
        "generic": {
            "format": f"{Colors.GREY}[%(process)s]{Colors.END}{Colors.BOLD}%(levelname)s:{Colors.END}\033[1000D\033[15C %(message)s",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
            "class": "logging.Formatter",
        },
        "access": {
            "format": f"{Colors.GREY}%(host)s {Colors.BLUE}%(request)s{Colors.END} %(message)s\033[1000C\033[39D\033[K %(status)s %(byte)s{Colors.GREY}%(duration)s{Colors.END}",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
            "class": "logging.Formatter",
        },
    },
)
"""
Defult logging configuration
"""


class VerbosityFilter(logging.Filter):
    verbosity: int = 0

    def filter(self, record: logging.LogRecord) -> bool:
        verbosity = getattr(record, "verbosity", 0)
        return verbosity <= self.verbosity


_verbosity_filter = VerbosityFilter()

logger = logging.getLogger("sanic.root")  # no cov
"""
General Sanic logger
"""
logger.addFilter(_verbosity_filter)

error_logger = logging.getLogger("sanic.error")  # no cov
"""
Logger used by Sanic for error logging
"""
error_logger.addFilter(_verbosity_filter)

access_logger = logging.getLogger("sanic.access")  # no cov
"""
Logger used by Sanic for access logging
"""
access_logger.addFilter(_verbosity_filter)

server_logger = logging.getLogger("sanic.server")  # no cov
"""
Logger used by Sanic for server related messages
"""
server_logger.addFilter(_verbosity_filter)

websockets_logger = logging.getLogger("sanic.websockets")  # no cov
"""
Logger used by Sanic for websockets module and protocol related messages
"""
websockets_logger.addFilter(_verbosity_filter)
websockets_logger.setLevel(logging.WARNING)  # Too noisy on debug/info


def deprecation(message: str, version: float):  # no cov
    """
    Add a deprecation notice

    Example when a feature is being removed. In this case, version
    should be AT LEAST next version + 2

        deprecation("Helpful message", 99.9)

    Example when a feature is deprecated but not being removed:

        deprecation("Helpful message", 0)

    :param message: The message of the notice
    :type message: str
    :param version: The version when the feature will be removed. If it is
      not being removed, then set version=0.
    :type version: float
    """
    version_display = f" v{version}" if version else ""
    version_info = f"[DEPRECATION{version_display}] "
    if is_atty():
        version_info = f"{Colors.RED}{version_info}"
        message = f"{Colors.YELLOW}{message}{Colors.END}"
    warn(version_info + message, DeprecationWarning)
