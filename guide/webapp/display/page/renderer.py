from __future__ import annotations

from contextlib import contextmanager
from typing import Type

from webapp.display.base import BaseRenderer

from html5tagger import HTML, Builder  # type: ignore
from sanic import Request

from ..layouts.base import BaseLayout
from .page import Page


class PageRenderer(BaseRenderer):
    def render(self, request: Request, language: str, path: str) -> Builder:
        builder = self.get_builder(
            full=request.headers.get("HX-Request") is None,
            language=language,
        )
        self._body(request, builder, language, path)
        return builder

    def _body(
        self, request: Request, builder: Builder, language: str, path: str
    ):
        prev_page, current_page, next_page = Page.get(language, path)
        request.ctx.language = (
            Page.DEFAULT_LANGUAGE if language == "api" else language
        )
        request.ctx.current_page = current_page
        request.ctx.previous_page = prev_page
        request.ctx.next_page = next_page
        with self._base(request, builder, current_page):
            if current_page is None:
                builder.h1("Not found")
                return
            builder(HTML(current_page.content))

    @contextmanager
    def _base(self, request: Request, builder: Builder, page: Page | None):
        layout_type: Type[BaseLayout] = (
            page.get_layout() if page else BaseLayout
        )
        layout = layout_type(builder)
        with layout(request, builder.full):
            yield
