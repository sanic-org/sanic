from __future__ import annotations

import importlib
import inspect
import pkgutil
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from html import escape
from pathlib import Path
from typing import Type

from frontmatter import parse
from rich import print

from html5tagger import HTML, Builder, Document, E  # type: ignore
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
DEFAULT = "en"


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
        print(self._relative_path)
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

        for section, items in _PAGE_CACHE.items():
            print(f"[bold yellow]{section}[/bold yellow]")
            for name, (prev, current, next) in items.items():
                print(f"\t[cyan]{name}[/cyan]")

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

    @staticmethod
    def _load_api_pages() -> dict[str, Page]:
        docstring_content = _organize_docobjects("sanic")
        output: dict[str, Page] = {}

        for module, content in docstring_content.items():
            page = Page(
                path=Path(module),
                content=content,
                meta=PageMeta(
                    title=module,
                    description="",
                    layout="main",
                ),
            )
            page._relative_path = Path(f"./{module}")
            output[module] = page

        return output


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
        request.ctx.language = DEFAULT if language == "api" else language
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


@dataclass
class DocObject:
    name: str
    module_name: str
    signature: inspect.Signature | None
    docstring: str
    methods: list[DocObject] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)


def _extract_docobjects(package_name: str) -> dict[str, DocObject]:
    docstrings = {}
    package = importlib.import_module(package_name)
    signature: inspect.Signature | None
    for _, name, _ in pkgutil.walk_packages(
        package.__path__, package_name + "."
    ):
        module = importlib.import_module(name)
        for obj_name, obj in inspect.getmembers(module):
            if inspect.getmodule(obj) == module and callable(obj):
                try:
                    signature = inspect.signature(obj)
                    docstring = inspect.getdoc(obj)
                    docstrings[f"{name}.{obj_name}"] = DocObject(
                        name=obj_name,
                        module_name=name,
                        signature=signature,
                        docstring=docstring or "",
                    )
                    if inspect.isclass(obj):
                        methods: list[DocObject] = []
                        for method_name, method in inspect.getmembers(
                            obj, is_public_member
                        ):
                            try:
                                signature = inspect.signature(method)
                            except TypeError:
                                signature = None
                            docstring = inspect.getdoc(method)
                            methods.append(
                                DocObject(
                                    name=method_name,
                                    module_name="",
                                    signature=signature,
                                    docstring=docstring or "",
                                    decorators=_detect_decorators(obj, method),
                                )
                            )
                        docstrings[f"{name}.{obj_name}"].methods = methods
                except ValueError:
                    pass
    return docstrings


def is_public_member(obj):
    return not getattr(obj, "__name__", "").startswith("_") and (
        inspect.ismethod(obj)
        or inspect.isfunction(obj)
        or isinstance(obj, property)
        or isinstance(obj, property)
    )


def _organize_docobjects(package_name: str) -> dict[str, str]:
    page_content: defaultdict[str, str] = defaultdict(str)
    docobjects = _extract_docobjects(package_name)
    for module, docobject in docobjects.items():
        ref = module.rsplit(".", module.count(".") - 1)[0]
        page_content[f"/api/{ref}.md"] += _docobject_to_html(docobject)
    return page_content


def _docobject_to_html(docobject: DocObject) -> str:
    builder = Builder(name="Partial")
    body = render_markdown(docobject.docstring)
    with builder.div(class_="docobject"):
        builder.h2(
            E.span(docobject.module_name, class_="has-text-weight-light"),
            ".",
            E.span(docobject.name, class_="has-text-weight-bold"),
            class_="is-size-2",
        ).p(
            HTML(_signature_to_html(docobject.name, docobject.signature, [])),
            class_="signature notification is-family-monospace",
        )(
            HTML(body)
        )
        if docobject.methods:
            with builder.div(class_="methods"):
                for method in docobject.methods:
                    builder.h3(
                        method.name,
                        class_="is-size-4 has-text-weight-bold mt-6",
                    ).p(
                        HTML(
                            _signature_to_html(
                                method.name,
                                method.signature,
                                method.decorators,
                            )
                        ),
                        class_="signature notification is-family-monospace",
                    )(
                        HTML(render_markdown(method.docstring))
                    )
    return str(builder)


def _signature_to_html(
    name: str, signature: inspect.Signature | None, decorators: list[str]
) -> str:
    parts = []
    parts.append("<span class='function-signature'>")
    for decorator in decorators:
        parts.append(f"@{decorator}<br>")
    parts.append(f"{name}(")
    if not signature:
        parts.append("<span class='param-name'>self</span>)")
        parts.append("</span>")
        return "".join(parts)
    for i, param in enumerate(signature.parameters.values()):
        parts.append(f"<span class='param-name'>{escape(param.name)}</span>")
        if param.annotation != inspect.Parameter.empty:
            annotation = escape(str(param.annotation))
            parts.append(
                f": <span class='param-annotation'>{annotation}</span>"
            )
        if param.default != inspect.Parameter.empty:
            default = escape(str(param.default))
            parts.append(f" = <span class='param-default'>{default}</span>")
        if i < len(signature.parameters) - 1:
            parts.append(", ")
    parts.append(")")
    if signature.return_annotation != inspect.Signature.empty:
        return_annotation = escape(str(signature.return_annotation))
        parts.append(
            f": -> <span class='return-annotation'>{return_annotation}</span>"
        )
    parts.append("</span>")
    return "".join(parts)


def _detect_decorators(cls, method):
    decorators = []
    method_name = getattr(method, "__name__", None)
    if isinstance(cls.__dict__.get(method_name), classmethod):
        decorators.append("classmethod")
    if isinstance(cls.__dict__.get(method_name), staticmethod):
        decorators.append("staticmethod")
    if isinstance(method, property):
        decorators.append("property")
    return decorators
