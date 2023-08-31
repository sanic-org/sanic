from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from html5tagger import Builder
from sanic import Request


class BaseLayout:
    def __init__(self, builder: Builder):
        self.builder = builder

    @contextmanager
    def __call__(
        self, request: Request, full: bool = True
    ) -> Generator[BaseLayout, None, None]:
        with self.layout(request, full=full):
            yield self

    @contextmanager
    def layout(
        self, request: Request, full: bool = True
    ) -> Generator[None, None, None]:
        yield
