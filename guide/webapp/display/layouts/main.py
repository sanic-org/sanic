from contextlib import contextmanager
from typing import Generator

from webapp.display.layouts.elements.footer import do_footer
from webapp.display.layouts.elements.navbar import do_navbar
from webapp.display.layouts.elements.sidebar import do_sidebar

from sanic import Request

from .base import BaseLayout


class MainLayout(BaseLayout):
    @contextmanager
    def layout(
        self, request: Request, full: bool = True
    ) -> Generator[None, None, None]:
        if full:
            self.builder.div(class_="loading-bar")
            with self.builder.div(class_="is-flex"):
                self._sidebar(request)
                with self.builder.main(class_="is-flex-grow-1"):
                    self._navbar(request)
                    with self.builder.div(class_="container", id="content"):
                        with self._content_wrapper():
                            yield
                        self._footer(request)
        else:
            with self._content_wrapper():
                yield
            self._footer(request)

    @contextmanager
    def _content_wrapper(self) -> Generator[None, None, None]:
        with self.builder.section(class_="section"):
            with self.builder.article():
                yield

    def _navbar(self, request: Request) -> None:
        do_navbar(self.builder, request)

    def _sidebar(self, request: Request) -> None:
        do_sidebar(self.builder, request)

    def _footer(self, request: Request) -> None:
        do_footer(self.builder, request)
