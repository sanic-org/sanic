from sys import argv

from multidict import CIMultiDict  # type: ignore
from asyncio import CancelledError

try:
    from trio import Cancelled
    CancelledErrors = CancelledError, Cancelled
except ImportError:
    CancelledErrors = CancelledError,

class Header(CIMultiDict):
    def get_all(self, key):
        return self.getall(key, default=[])


use_trio = argv[0].endswith("hypercorn") and "trio" in argv

if use_trio:
    from trio import open_file as open_async, Path  # type: ignore

    def stat_async(path):
        return Path(path).stat()


else:
    from aiofiles import open as aio_open  # type: ignore
    from aiofiles.os import stat as stat_async  # type: ignore  # noqa: F401

    async def open_async(file, mode="r", **kwargs):
        return aio_open(file, mode, **kwargs)
