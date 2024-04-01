import logging

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


def setup_logging(debug: bool) -> None:
    if AutoFormatter.SETUP:
        return

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
