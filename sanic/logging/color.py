import logging
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


class Colors(StrEnum):  # no cov
    END = "\033[0m" if is_atty() else ""
    BOLD = "\033[1m" if is_atty() else ""
    BLUE = "\033[34m" if is_atty() else ""
    GREEN = "\033[32m" if is_atty() else ""
    PURPLE = "\033[35m" if is_atty() else ""
    RED = "\033[31m" if is_atty() else ""
    SANIC = "\033[38;2;255;13;104m" if is_atty() else ""
    YELLOW = "\033[01;33m" if is_atty() else ""
    GREY = "\033[38;5;240m" if is_atty() else ""


LEVEL_COLORS = {
    logging.DEBUG: Colors.BLUE,
    logging.INFO: Colors.GREEN,
    logging.WARNING: Colors.YELLOW,
    logging.ERROR: Colors.RED,
    logging.CRITICAL: Colors.RED + Colors.BOLD,
}
