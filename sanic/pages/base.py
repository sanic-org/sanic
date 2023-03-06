from abc import ABC, abstractmethod

from html5tagger import HTML, Builder, Document, E
from sanic import __version__ as VERSION
from sanic.application.logo import SVG_LOGO_SIMPLE
from sanic.pages.css import CSS


class BasePage(ABC, metaclass=CSS):  # no cov
    TITLE = "Sanic"
    HEADING = None
    CSS: str
    doc: Builder

    def __init__(self, debug: bool = True) -> None:
        self.debug = debug

    @property
    def style(self) -> str:
        return self.CSS

    def render(self) -> str:
        self.doc = Document(self.TITLE, lang="en", id="sanic")
        self._head()
        self._body()
        self._foot()
        return str(self.doc)

    def _head(self) -> None:
        self.doc.style(HTML(self.style))
        with self.doc.header:
            self.doc.div(self.HEADING or self.TITLE)

    def _foot(self) -> None:
        with self.doc.footer:
            self.doc.div("powered by")
            with self.doc.div:
                self._sanic_logo()
            if self.debug:
                pages = (
                    ("Docs", "https://sanic.dev"),
                    ("Help", "https://sanic.dev"),
                    ("GitHub", "https://sanic.dev"),
                    ("Discord", "https://sanic.dev"),
                )
                inner = [
                    items
                    for idx, (title, href) in enumerate(pages)
                    for items in [
                        "" if idx == 0 else " | ",
                        E.a(
                            title,
                            href=href,
                            target="_blank",
                            referrerpolicy="no-referrer",
                        ),
                    ]
                ]
                self.doc.div(f"Version {VERSION}").div(*inner).div(
                    "DEBUG mode"
                )

    @abstractmethod
    def _body(self) -> None:
        ...

    def _sanic_logo(self) -> None:
        self.doc.a(
            HTML(SVG_LOGO_SIMPLE),
            href="https://sanic.dev",
            target="_blank",
            referrerpolicy="no-referrer",
        )
