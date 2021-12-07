import logging
import pytest

from sanic.server import loop
from sanic.compat import OS_IS_WINDOWS, UVLOOP_INSTALLED


@pytest.mark.skipif(
    not OS_IS_WINDOWS,
    reason="Not testable with current client",
)
def test_raises_warning_if_os_is_windows(caplog):
    with caplog.at_level(logging.WARNING):
        loop.try_use_uvloop()

    for record in caplog.records:
        if record.message.startswith("You are trying to use"):
            break

    assert record.message == (
        "You are trying to use uvloop, but uvloop is not compatible "
        "with your system. You can disable uvloop completely by setting "
        "the 'USE_UVLOOP' configuration value to false, or simply not "
        "defining it and letting Sanic handle it for you. Sanic will now "
        "continue to run using the default event loop."
    )


@pytest.mark.skipif(
    OS_IS_WINDOWS,
    reason="Not testable with current client",
)
def test_raises_warning_if_uvloop_not_installed(caplog):
    if not UVLOOP_INSTALLED:
        with caplog.at_level(logging.WARNING):
            loop.try_use_uvloop()

        for record in caplog.records:
            if record.message.startswith("You are trying to use"):
                break

        assert record.message == (
            "You are trying to use uvloop, but uvloop is not "
            "installed in your system. In order to use uvloop "
            "you must first install it. Otherwise, you can disable "
            "uvloop completely by setting the 'USE_UVLOOP' "
            "configuration value to false. Sanic will now continue "
            "to run with the default event loop."
        )
