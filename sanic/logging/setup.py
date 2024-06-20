import logging
import os

from typing import Type

from sanic.log import (
    access_logger,
    error_logger,
    logger,
    server_logger,
    websockets_logger,
)
from sanic.logging.formatter import (
    AutoAccessFormatter,
    AutoFormatter,
    DebugAccessFormatter,
    DebugFormatter,
    ProdAccessFormatter,
    ProdFormatter,
)


def setup_logging(
    debug: bool, no_color: bool = False, log_extra: bool = True
) -> None:
    if AutoFormatter.SETUP:
        return

    if no_color:
        os.environ["SANIC_NO_COLOR"] = str(no_color)
        AutoFormatter.NO_COLOR = no_color
    if not log_extra:
        os.environ["SANIC_LOG_EXTRA"] = str(log_extra)
        AutoFormatter.LOG_EXTRA = log_extra
    AutoFormatter.SETUP = True
    for lggr in (logger, server_logger, error_logger, websockets_logger):
        _auto_format(
            lggr,
            AutoFormatter,
            DebugFormatter if debug else ProdFormatter,
        )
    _auto_format(
        access_logger,
        AutoAccessFormatter,
        DebugAccessFormatter if debug else ProdAccessFormatter,
    )


def _auto_format(
    logger: logging.Logger,
    auto_class: Type[AutoFormatter],
    formatter_class: Type[AutoFormatter],
) -> None:
    for handler in logger.handlers:
        if type(handler.formatter) is auto_class:
            handler.setFormatter(formatter_class())
