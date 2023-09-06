from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Type

from frontmatter import parse

from ..layouts.base import BaseLayout
from ..layouts.home import HomeLayout
from ..layouts.main import MainLayout
from ..markdown import render_markdown
from .docobject import organize_docobjects

_PAGE_CACHE: dict[
    str, dict[str, tuple[Page | None, Page | None, Page | None]]
] = {}
_LAYOUTS_CACHE: dict[str, Type[BaseLayout]] = {
    "home": HomeLayout,
    "main": MainLayout,
}
_DEFAULT = "en"


@dataclass
class PageMeta:
    language: str = _DEFAULT
    title: str = ""
    description: str = ""
    layout: str = "main"
    features: list[dict[str, str]] = field(default_factory=list)


@dataclass
class Page:
    path: Path
    content: str
    meta: PageMeta = field(default_factory=PageMeta)
    _relative_path: Path | None = None
    next_page: Page | None = None
    previous_page: Page | None = None
    anchors: list[str] = field(default_factory=list)

    DEFAULT_LANGUAGE = _DEFAULT

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
        if language == "api":
            path = f"/api/{path}"
        return _PAGE_CACHE.get(language, {}).get(path, (None, None, None))

    @classmethod
    def load_pages(cls, base_path: Path, page_order: list[str]) -> list[Page]:
        output: list[Page] = []
        for path in base_path.glob("**/*.md"):
            relative = path.relative_to(base_path)
            language = relative.parts[0]
            name = "/".join(relative.parts[1:])
            page = cls._load_page(path)
            output.append(page)
            page._relative_path = relative
            _PAGE_CACHE.setdefault(language, {})[name] = (
                None,
                page,
                None,
            )
            _PAGE_CACHE["api"] = {}
        for language, pages in _PAGE_CACHE.items():
            for name, (_, current, _) in pages.items():
                previous_page = None
                next_page = None
                try:
                    index = page_order.index(name)
                except ValueError:
                    continue
                try:
                    if index > 0:
                        previous_page = pages[page_order[index - 1]][1]
                except KeyError:
                    pass
                try:
                    if index < len(page_order) - 1:
                        next_page = pages[page_order[index + 1]][1]
                except KeyError:
                    pass
                pages[name] = (previous_page, current, next_page)
            previous_page = None
            next_page = None

        api_pages = cls._load_api_pages()
        filtered_order = [ref for ref in page_order if ref in api_pages]
        for idx, ref in enumerate(filtered_order):
            current_page = api_pages[ref]
            previous_page = None
            next_page = None
            try:
                if idx > 0:
                    previous_page = api_pages[filtered_order[idx - 1]]
            except KeyError:
                pass
            try:
                if idx < len(filtered_order) - 1:
                    next_page = api_pages[filtered_order[idx + 1]]
            except KeyError:
                pass
            _PAGE_CACHE["api"][ref] = (previous_page, current_page, next_page)

        return output

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
            if line.startswith("##") and not line.startswith("###"):
                line = line.lstrip("#").strip()
                page.anchors.append(line)

        return page

    @staticmethod
    def _load_api_pages() -> dict[str, Page]:
        docstring_content = organize_docobjects("sanic")
        output: dict[str, Page] = {}

        for module, content in docstring_content.items():
            path = Path(module)
            page = Page(
                path=path,
                content=content,
                meta=PageMeta(
                    title=path.stem,
                    description="",
                    layout="main",
                ),
            )
            page._relative_path = Path(f"./{module}")
            output[module] = page

        return output
