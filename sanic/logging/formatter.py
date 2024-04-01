from __future__ import annotations

import logging
import os
import re

from sanic.helpers import is_atty
from sanic.logging.color import LEVEL_COLORS, Colors


CONTROL_RE = re.compile(r"\033\[[0-9;]*\w")
CONTROL_LIMIT_IDENT = "\033[1000D\033[{limit}C"
CONTROL_LIMIT_START = "\033[1000D\033[{start}C\033[K"
CONTROL_LIMIT_END = "\033[1000C\033[{right}D\033[K"


class AutoFormatter(logging.Formatter):
    """
    Automatically sets up the formatter based on the environment.

    It will switch between the Debug and Production formatters based upon
    how the environment is set up. Additionally, it will automatically
    detect if the output is a TTY and colorize the output accordingly.
    """

    SETUP = False
    ATTY = is_atty()
    IDENT = os.environ.get("SANIC_WORKER_IDENTIFIER", "Main ")
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S %z"
    PREFIX_FORMAT = (
        f"{Colors.GREY}%(ident)s{{limit}}|{Colors.END}%(levelname)s: {{start}}"
    )
    MESSAGE_FORMAT = "%(message)s"
    IDENT_LIMIT = -1
    MESSAGE_START = 11

    def __init__(self, *args) -> None:
        args_list = list(args)
        if not args:
            args_list.append(self._make_format())
        elif args and not args[0]:
            args_list[0] = self._make_format()
        if len(args_list) < 2:
            args_list.append(self.DATE_FORMAT)
        elif not args[1]:
            args_list[1] = self.DATE_FORMAT

        super().__init__(*args_list)

    def format(self, record: logging.LogRecord) -> str:
        record.ident = self.IDENT
        self._set_levelname(record)
        return super().format(record)

    def _set_levelname(self, record: logging.LogRecord) -> None:
        if self.ATTY and (color := LEVEL_COLORS.get(record.levelno)):
            record.levelname = f"{color}{record.levelname}{Colors.END}"

    def _make_format(self) -> str:
        limit = CONTROL_LIMIT_IDENT.format(limit=self.IDENT_LIMIT)
        start = CONTROL_LIMIT_START.format(start=self.MESSAGE_START)
        base_format = self.PREFIX_FORMAT + self.MESSAGE_FORMAT
        fmt = base_format.format(limit=limit, start=start)
        if not self.ATTY:
            return CONTROL_RE.sub("", fmt)
        return fmt


class DebugFormatter(AutoFormatter):
    """
    The DebugFormatter is used for development and debugging purposes.

    It can be used directly, or it will be automatically selected if the
    environment is set up for development and is using the AutoFormatter.
    """

    IDENT_LIMIT = 5
    MESSAGE_START = 13

    def _set_levelname(self, record: logging.LogRecord) -> None:
        if len(record.levelname) > 5:
            record.levelname = record.levelname[:4]
        super()._set_levelname(record)


class ProdFormatter(AutoFormatter):
    """
    The ProdFormatter is used for production environments.

    It can be used directly, or it will be automatically selected if the
    environment is set up for production and is using the AutoFormatter.
    """

    IDENT_LIMIT = 5
    MESSAGE_START = 42
    PREFIX_FORMAT = (
        f"{Colors.GREY}%(ident)s{{limit}}|%(asctime)s|{Colors.END}"
        "%(levelname)s: {start}"
    )


class LegacyFormatter(AutoFormatter):
    """
    The LegacyFormatter is used if you want to use the old style of logging.

    You can use it as follows, typically in conjunction with the
    LegacyAccessFormatter:

    .. code-block:: python

        from sanic.log import LOGGING_CONFIG_DEFAULTS

        LOGGING_CONFIG_DEFAULTS["formatters"] = {
            "generic": {
                "class": "sanic.logging.formatter.LegacyFormatter"
            },
            "access": {
                "class": "sanic.logging.formatter.LegacyAccessFormatter"
            },
        }
    """

    PREFIX_FORMAT = "%(asctime)s [%(process)s] [%(levelname)s] "
    DATE_FORMAT = "[%Y-%m-%d %H:%M:%S %z]"


class AutoAccessFormatter(AutoFormatter):
    MESSAGE_FORMAT = (
        f"%(asctime)s {Colors.PURPLE}%(host)s "
        f"{Colors.BLUE + Colors.BOLD}%(request)s{Colors.END} "
        f"%(right)s%(status)s %(byte)s {Colors.GREY}%(duration)s{Colors.END}"
    )

    def format(self, record: logging.LogRecord) -> str:
        status = len(str(getattr(record, "status", "")))
        byte = len(str(getattr(record, "byte", "")))
        duration = len(str(getattr(record, "duration", "")))
        record.right = (
            CONTROL_LIMIT_END.format(right=status + byte + duration + 1)
            if self.ATTY
            else ""
        )
        return super().format(record)

    def _set_levelname(self, record: logging.LogRecord) -> None:
        if self.ATTY and record.levelno == logging.INFO:
            record.levelname = f"{Colors.SANIC}ACCESS{Colors.END}"


class LegacyAccessFormatter(AutoAccessFormatter):
    """
    The LegacyFormatter is used if you want to use the old style of logging.

    You can use it as follows, typically in conjunction with the
    LegacyFormatter:

    .. code-block:: python

        from sanic.log import LOGGING_CONFIG_DEFAULTS

        LOGGING_CONFIG_DEFAULTS["formatters"] = {
            "generic": {
                "class": "sanic.logging.formatter.LegacyFormatter"
            },
            "access": {
                "class": "sanic.logging.formatter.LegacyAccessFormatter"
            },
        }
    """

    PREFIX_FORMAT = "%(asctime)s - (%(name)s)[%(levelname)s][%(host)s]: "
    MESSAGE_FORMAT = "%(request)s %(message)s %(status)s %(byte)s"


class DebugAccessFormatter(AutoAccessFormatter):
    IDENT_LIMIT = 5
    MESSAGE_START = 16
    DATE_FORMAT = "%H:%M:%S"


class ProdAccessFormatter(AutoAccessFormatter):
    IDENT_LIMIT = 5
    MESSAGE_START = 42
    PREFIX_FORMAT = (
        f"{Colors.GREY}%(ident)s{{limit}}|%(asctime)s{Colors.END} "
        f"%(levelname)s: {{start}}"
    )
    MESSAGE_FORMAT = (
        f"{Colors.PURPLE}%(host)s {Colors.BLUE + Colors.BOLD}"
        f"%(request)s{Colors.END} "
        f"%(right)s%(status)s %(byte)s {Colors.GREY}%(duration)s{Colors.END}"
    )
