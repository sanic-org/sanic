import logging

import pytest

from sanic.signals import RESERVED_NAMESPACES
from sanic.touchup import TouchUp


def test_touchup_methods(app):
    assert len(TouchUp._registry) == 9


@pytest.mark.parametrize(
    "verbosity,result", ((0, False), (1, False), (2, True), (3, True))
)
async def test_ode_removes_dispatch_events(app, caplog, verbosity, result):
    with caplog.at_level(logging.DEBUG, logger="sanic.root"):
        app.state.verbosity = verbosity
        await app._startup()
    logs = caplog.record_tuples

    for signal in RESERVED_NAMESPACES["http"]:
        assert (
            (
                "sanic.root",
                logging.DEBUG,
                f"Disabling event: {signal}",
            )
            in logs
        ) is result
