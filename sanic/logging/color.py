import logging
import os
import sys

from enum import Enum
from typing import TYPE_CHECKING

from sanic.helpers import is_atty


# Python 3.11 changed the way Enum formatting works for mixed-in types.
if sys.version_info < (3, 11, 0):

    class StrEnum(str, Enum):
        pass

else:
    if not TYPE_CHECKING:
        from enum import StrEnum


COLORIZE = is_atty() and not os.environ.get("SANIC_NO_COLOR")


class Colors(StrEnum):  # no cov
    """
    Colors for log messages. If the output is not a TTY, the colors will be
    disabled.

    Can be used like this:

    .. code-block:: python

        from sanic.log import logger, Colors

        logger.info(f"{Colors.GREEN}This is a green message{Colors.END}")


    Attributes:
        END: Reset the color
        BOLD: Bold text
        BLUE: Blue text
        GREEN: Green text
        PURPLE: Purple text
        RED: Red text
        SANIC: Sanic pink
        YELLOW: Yellow text
        GREY: Grey text
    """

    END = "\033[0m" if COLORIZE else ""
    BOLD = "\033[1m" if COLORIZE else ""
    BLUE = "\033[34m" if COLORIZE else ""
    GREEN = "\033[32m" if COLORIZE else ""
    PURPLE = "\033[35m" if COLORIZE else ""
    CYAN = "\033[36m" if COLORIZE else ""
    RED = "\033[31m" if COLORIZE else ""
    YELLOW = "\033[33m" if COLORIZE else ""
    GREY = "\033[38;5;240m" if COLORIZE else ""
    SANIC = "\033[38;2;255;13;104m" if COLORIZE else ""


LEVEL_COLORS = {
    logging.DEBUG: Colors.BLUE,
    logging.WARNING: Colors.YELLOW,
    logging.ERROR: Colors.RED,
    logging.CRITICAL: Colors.RED + Colors.BOLD,
}
