import logging
import sys

from enum import Enum
from typing import TYPE_CHECKING, Any, Dict
from warnings import warn

from sanic.compat import is_atty


# Python 3.11 changed the way Enum formatting works for mixed-in types.
if sys.version_info < (3, 11, 0):

    class StrEnum(str, Enum):
        pass

else:
    if not TYPE_CHECKING:
        from enum import StrEnum


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
            "format": "%(asctime)s [%(process)d] [%(levelname)s] %(message)s",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
            "class": "logging.Formatter",
        },
        "access": {
            "format": "%(asctime)s - (%(name)s)[%(levelname)s][%(host)s]: "
            + "%(request)s %(message)s %(status)d %(byte)d",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
            "class": "logging.Formatter",
        },
    },
)
"""
Defult logging configuration
"""


class Colors(StrEnum):  # no cov
    END = "\033[0m"
    BOLD = "\033[1m"
    BLUE = "\033[34m"
    GREEN = "\033[32m"
    PURPLE = "\033[35m"
    RED = "\033[31m"
    SANIC = "\033[38;2;255;13;104m"
    YELLOW = "\033[01;33m"


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
logger.addFilter(_verbosity_filter)


def deprecation(message: str, version: float):  # no cov
    version_info = f"[DEPRECATION v{version}] "
    if is_atty():
        version_info = f"{Colors.RED}{version_info}"
        message = f"{Colors.YELLOW}{message}{Colors.END}"
    warn(version_info + message, DeprecationWarning)
