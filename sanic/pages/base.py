from abc import ABC, abstractmethod

from html5tagger import HTML, Document

from sanic import __version__ as VERSION
from sanic.application.logo import SVG_LOGO
from sanic.pages.css import CSS


class BasePage(ABC, metaclass=CSS):  # no cov
    TITLE = "Unknown"
    CSS: str

    def __init__(self, debug: bool = True) -> None:
        self.doc = Document(self.TITLE, lang="en")
        self.debug = debug

    @property
    def style(self) -> str:
        return self.CSS

    def render(self) -> str:
        self._head()
        self._body()
        self._foot()
        return str(self.doc)

    def _head(self) -> None:
        self.doc.style(HTML(self.style))
        with self.doc.header:
            self.doc.div(self.TITLE)

    def _foot(self) -> None:
        with self.doc.footer:
            self.doc.div("powered by")
            with self.doc.div:
                self._sanic_logo()
            if self.debug:
                self.doc.div(f"Version {VERSION}")

    @abstractmethod
    def _body(self) -> None:
        ...

    def _sanic_logo(self) -> None:
        self.doc.a(
            HTML(SVG_LOGO),
            href="https://sanic.dev",
            target="_blank",
            referrerpolicy="no-referrer",
        )
