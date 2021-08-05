import logging

from sanic.signals import RESERVED_NAMESPACES
from sanic.touchup import TouchUp


def test_touchup_methods(app):
    assert len(TouchUp._registry) == 9


async def test_ode_removes_dispatch_events(app, caplog):
    with caplog.at_level(logging.DEBUG, logger="sanic.root"):
        await app._startup()
    logs = caplog.record_tuples

    for signal in RESERVED_NAMESPACES["http"]:
        assert (
            "sanic.root",
            logging.DEBUG,
            f"Disabling event: {signal}",
        ) in logs
