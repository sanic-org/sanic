import asyncio
import os
import signal
import sys

from typing import Awaitable

from multidict import CIMultiDict  # type: ignore


OS_IS_WINDOWS = os.name == "nt"
UVLOOP_INSTALLED = False

try:
    import uvloop  # type: ignore # noqa

    UVLOOP_INSTALLED = True
except ImportError:
    pass


def enable_windows_color_support():
    import ctypes

    kernel = ctypes.windll.kernel32
    kernel.SetConsoleMode(kernel.GetStdHandle(-11), 7)


class Header(CIMultiDict):
    """
    Container used for both request and response headers. It is a subclass of
    `CIMultiDict
    <https://multidict.readthedocs.io/en/stable/multidict.html#cimultidictproxy>`_.

    It allows for multiple values for a single key in keeping with the HTTP
    spec. Also, all keys are *case in-sensitive*.

    Please checkout `the MultiDict documentation
    <https://multidict.readthedocs.io/en/stable/multidict.html#multidict>`_
    for more details about how to use the object. In general, it should work
    very similar to a regular dictionary.
    """

    def get_all(self, key: str):
        """
        Convenience method mapped to ``getall()``.
        """
        return self.getall(key, default=[])


use_trio = sys.argv[0].endswith("hypercorn") and "trio" in sys.argv

if use_trio:  # pragma: no cover
    import trio  # type: ignore

    def stat_async(path) -> Awaitable[os.stat_result]:
        return trio.Path(path).stat()

    open_async = trio.open_file
    CancelledErrors = tuple([asyncio.CancelledError, trio.Cancelled])
else:
    from aiofiles import open as aio_open  # type: ignore
    from aiofiles.os import stat as stat_async  # type: ignore  # noqa: F401

    async def open_async(file, mode="r", **kwargs):
        return aio_open(file, mode, **kwargs)

    CancelledErrors = tuple([asyncio.CancelledError])


def ctrlc_workaround_for_windows(app):
    async def stay_active(app):
        """Asyncio wakeups to allow receiving SIGINT in Python"""
        while not die:
            # If someone else stopped the app, just exit
            if app.state.is_stopping:
                return
            # Windows Python blocks signal handlers while the event loop is
            # waiting for I/O. Frequent wakeups keep interrupts flowing.
            await asyncio.sleep(0.1)
        # Can't be called from signal handler, so call it from here
        app.stop()

    def ctrlc_handler(sig, frame):
        nonlocal die
        if die:
            raise KeyboardInterrupt("Non-graceful Ctrl+C")
        die = True

    die = False
    signal.signal(signal.SIGINT, ctrlc_handler)
    app.add_task(stay_active)


def is_atty() -> bool:
    return bool(sys.stdout and sys.stdout.isatty())
