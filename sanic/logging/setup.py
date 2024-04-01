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
    SanicAutoAccessFormatter,
    SanicAutoFormatter,
    SanicDebugAccessFormatter,
    SanicDebugFormatter,
    SanicProdAccessFormatter,
    SanicProdFormatter,
)


def setup_logging(debug: bool) -> None:
    if SanicAutoFormatter.SETUP:
        return

    SanicAutoFormatter.SETUP = True
    for lggr in (logger, server_logger, error_logger, websockets_logger):
        _auto_format(
            lggr,
            SanicAutoFormatter,
            SanicDebugFormatter if debug else SanicProdFormatter,
        )
    _auto_format(
        access_logger,
        SanicAutoAccessFormatter,
        SanicDebugAccessFormatter if debug else SanicProdAccessFormatter,
    )


def _auto_format(
    logger: logging.Logger,
    auto_class: Type[SanicAutoFormatter],
    formatter_class: Type[SanicAutoFormatter],
) -> None:
    for handler in logger.handlers:
        if type(handler.formatter) is auto_class:
            handler.setFormatter(formatter_class())
