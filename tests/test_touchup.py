import logging

import pytest

from sanic_routing.exceptions import NotFound

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


@pytest.mark.parametrize("skip_it,result", ((False, True), (True, False)))
async def test_skip_touchup(app, caplog, skip_it, result):
    app.config.SKIP_TOUCHUP = skip_it
    with caplog.at_level(logging.DEBUG, logger="sanic.root"):
        app.state.verbosity = 2
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
    not_found_exceptions = 0
    # Skip-touchup disables NotFound exceptions on the dispatcher
    for signal in RESERVED_NAMESPACES["http"]:
        try:
            await app.dispatch(event=signal, inline=True)
        except NotFound:
            not_found_exceptions += 1
    assert (not_found_exceptions > 0) is result
