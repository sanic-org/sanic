from contextlib import contextmanager
from urllib.parse import unquote

from webapp.display.search.search import Searcher

from html5tagger import Builder, E  # type: ignore
from sanic import Request

from ..base import BaseRenderer
from ..layouts.main import MainLayout


class SearchRenderer(BaseRenderer):
    def render(
        self, request: Request, language: str, searcher: Searcher, full: bool
    ) -> Builder:
        builder = self.get_builder(
            full=request.headers.get("HX-Request") is None,
            language=language,
        )
        self._body(request, builder, language, searcher, full)
        return builder

    def _body(
        self,
        request: Request,
        builder: Builder,
        language: str,
        searcher: Searcher,
        full: bool,
    ):
        with self._base(request, builder, full):
            builder.h1("Search")
            self._results(request, builder, searcher, language)

    @contextmanager
    def _base(self, request: Request, builder: Builder, full: bool):
        layout = MainLayout(builder)
        with layout(request, full):
            yield

    def _results(
        self,
        request: Request,
        builder: Builder,
        searcher: Searcher,
        language: str,
    ):
        query = unquote(request.args.get("q", ""))
        results = searcher.search(query, language)
        if not query or not results:
            builder.p("No results found")
            return

        with builder.div(class_="container"):
            with builder.ul():
                for _, doc in results:
                    builder.li(
                        E.a(
                            doc.title,
                            href=f"/{doc.page.relative_path}",
                            hx_get=f"/{doc.page.relative_path}",
                            hx_target="#content",
                            hx_swap="innerHTML",
                            hx_push_url="true",
                        ),
                        f" - {doc.page.relative_path}",
                    )
