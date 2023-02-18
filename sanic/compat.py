import asyncio
import os
import signal
import sys

from contextlib import contextmanager
from enum import Enum
from typing import Awaitable, Union

from multidict import CIMultiDict  # type: ignore

from sanic.helpers import Default


if sys.version_info < (3, 8):  # no cov
    StartMethod = Union[Default, str]
else:  # no cov
    from typing import Literal

    StartMethod = Union[
        Default, Literal["fork"], Literal["forkserver"], Literal["spawn"]
    ]

OS_IS_WINDOWS = os.name == "nt"
UVLOOP_INSTALLED = False

try:
    import uvloop  # type: ignore # noqa

    UVLOOP_INSTALLED = True
except ImportError:
    pass

# Python 3.11 changed the way Enum formatting works for mixed-in types.
if sys.version_info < (3, 11, 0):

    class StrEnum(str, Enum):
        pass

else:
    from enum import StrEnum  # type: ignore # noqa


class UpperStrEnum(StrEnum):
    def _generate_next_value_(name, start, count, last_values):
        return name.upper()

    def __eq__(self, value: object) -> bool:
        value = str(value).upper()
        return super().__eq__(value)

    def __hash__(self) -> int:
        return hash(self.value)

    def __str__(self) -> str:
        return self.value


@contextmanager
def use_context(method: StartMethod):
    from sanic import Sanic

    orig = Sanic.start_method
    Sanic.start_method = method
    yield
    Sanic.start_method = orig


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
