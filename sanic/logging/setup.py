import logging

from typing import Type

from sanic.log import (
    access_logger,
    logger,
    server_logger,
    websockets_logger,
    error_logger,
)
from sanic.logging.formatter import (
    SanicAutoAccessFormatter,
    SanicAutoFormatter,
    SanicDebugAccessFormatter,
    SanicDebugFormatter,
    SanicProdAccessFormatter,
    SanicProdFormatter,
)


_setup_logging = False


def setup_logging(debug: bool) -> None:
    global _setup_logging

    if _setup_logging:
        return

    _setup_logging = True
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
