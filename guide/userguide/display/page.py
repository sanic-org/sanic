from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Type

from frontmatter import parse

from html5tagger import HTML, Builder, Document
from sanic import Request

from .layouts.base import BaseLayout
from .layouts.home import HomeLayout
from .layouts.main import MainLayout
from .markdown import render_markdown

_PAGE_CACHE: dict[
    str, dict[str, tuple[Page | None, Page | None, Page | None]]
] = {}
_LAYOUTS_CACHE: dict[str, Type[BaseLayout]] = {
    "home": HomeLayout,
    "main": MainLayout,
}


@dataclass
class PageMeta:
    title: str = ""
    description: str = ""
    layout: str = "main"


@dataclass
class Page:
    path: Path
    content: str
    meta: PageMeta
    _relative_path: Path | None = None
    next_page: Page | None = None
    previous_page: Page | None = None
    anchors: list[str] = field(default_factory=list)

    def get_layout(self) -> Type[BaseLayout]:
        return _LAYOUTS_CACHE[self.meta.layout]

    @property
    def relative_path(self) -> Path:
        if self._relative_path is None:
            raise RuntimeError("Page not initialized")
        return self._relative_path

    @classmethod
    def get(
        cls, language: str, path: str
    ) -> tuple[Page | None, Page | None, Page | None]:
        if path.endswith("/") or not path:
            path += "index.html"
        if not path.endswith(".md"):
            path = path.removesuffix(".html") + ".md"
        return _PAGE_CACHE.get(language, {}).get(path, (None, None, None))

    @classmethod
    def load_pages(cls, base_path: Path, page_order: list[str]) -> None:
        for path in base_path.glob("**/*.md"):
            relative = path.relative_to(base_path)
            language = relative.parts[0]
            name = "/".join(relative.parts[1:])
            page = cls._load_page(path)
            page._relative_path = relative
            _PAGE_CACHE.setdefault(language, {})[name] = (
                None,
                page,
                None,
            )
        for language, pages in _PAGE_CACHE.items():
            for name, (_, current, _) in pages.items():
                previous_page = None
                next_page = None
                try:
                    index = page_order.index(name)
                except ValueError:
                    continue
                if index > 0:
                    previous_page = pages[page_order[index - 1]][1]
                if index < len(page_order) - 1:
                    next_page = pages[page_order[index + 1]][1]
                pages[name] = (previous_page, current, next_page)

    @staticmethod
    def _load_page(path: Path) -> Page:
        raw = path.read_text()
        metadata, raw_content = parse(raw)
        content = render_markdown(raw_content)
        page = Page(
            path=path,
            content=content,
            meta=PageMeta(**metadata),
        )
        if not page.meta.title:
            page.meta.title = page.path.stem.replace("-", " ").title()

        for line in raw.splitlines():
            if line.startswith("#") and line.count("#") == 2:
                line = line.lstrip("#").strip()
                page.anchors.append(line)

        return page


class PageRenderer:
    def __init__(self, base_title: str):
        self.base_title = base_title

    def get_builder(self, full: bool, language: str) -> Builder:
        if full:
            urls = [
                "/assets/code.css",
                "/assets/style.css",
                "/assets/docs.js",
                "https://unpkg.com/htmx.org@1.9.2/dist/htmx.min.js",
            ]
            builder = Document(
                self.base_title, lang=language, _urls=urls, _viewport=True
            )
            builder.full = True
            return builder
        else:
            builder = Builder(name="Partial")
            builder.full = False
            return builder

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
        request.ctx.language = language
        request.ctx.current_page = current_page
        request.ctx.previous_page = prev_page
        request.ctx.next_page = next_page
        with self._base(request, builder, current_page):
            if current_page is None:
                builder.h1("Not found")
                return
            builder.raw(HTML(current_page.content))

    @contextmanager
    def _base(self, request: Request, builder: Builder, page: Page | None):
        layout_type: Type[BaseLayout] = (
            page.get_layout() if page else BaseLayout
        )
        layout = layout_type(builder)
        with layout(request, builder.full):
            yield
