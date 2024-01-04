from __future__ import annotations

import os

from typing import TYPE_CHECKING

from sanic.exceptions import (
    HeaderNotFound,
    InvalidRangeType,
    RangeNotSatisfiable,
)
from sanic.models.protocol_types import Range


if TYPE_CHECKING:
    from sanic import Request


class ContentRangeHandler(Range):
    """Parse and process the incoming request headers to extract the content range information.

    Args:
        request (Request): The incoming request object.
        stats (os.stat_result): The stats of the file being served.
    """  # noqa: E501

    __slots__ = ("start", "end", "size", "total", "headers")

    def __init__(self, request: Request, stats: os.stat_result) -> None:
        self.total = stats.st_size
        _range = request.headers.getone("range", None)
        if _range is None:
            raise HeaderNotFound("Range Header Not Found")
        unit, _, value = tuple(map(str.strip, _range.partition("=")))
        if unit != "bytes":
            raise InvalidRangeType(
                "%s is not a valid Range Type" % (unit,), self
            )
        start_b, _, end_b = tuple(map(str.strip, value.partition("-")))
        try:
            self.start = int(start_b) if start_b else None
        except ValueError:
            raise RangeNotSatisfiable(
                "'%s' is invalid for Content Range" % (start_b,), self
            )
        try:
            self.end = int(end_b) if end_b else None
        except ValueError:
            raise RangeNotSatisfiable(
                "'%s' is invalid for Content Range" % (end_b,), self
            )
        if self.end is None:
            if self.start is None:
                raise RangeNotSatisfiable(
                    "Invalid for Content Range parameters", self
                )
            else:
                # this case represents `Content-Range: bytes 5-`
                self.end = self.total - 1
        else:
            if self.start is None:
                # this case represents `Content-Range: bytes -5`
                self.start = self.total - self.end
                self.end = self.total - 1
        if self.start > self.end:
            raise RangeNotSatisfiable(
                "Invalid for Content Range parameters", self
            )
        self.size = self.end - self.start + 1
        self.headers = {
            "Content-Range": "bytes %s-%s/%s"
            % (self.start, self.end, self.total)
        }

    def __bool__(self):
        return hasattr(self, "size") and self.size > 0
