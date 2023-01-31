from abc import ABC, abstractmethod
from textwrap import dedent

from html5tagger import HTML, Document

from sanic import __version__ as VERSION
from sanic.application.logo import SVG_LOGO


class BasePage(ABC):  # no cov
    BASE_STYLE = dedent(
        """
        html { font: 16px monospace; }
        body { margin: 0; font-size: 1.25rem; }
        body > * { padding: 1rem 2vw; }
        @media (max-width:  1200px) {
            body > * { padding: 0.5rem 1.5vw;}
            body { font-size: 1rem; }
        }
        .container { min-width: 600px; max-width: 1600px; }
        header {
            background: #111; color: #e1e1e1; border-bottom: 1px solid #272727;
        }
        header .container {
            display: flex; align-items: center; justify-content: space-between;
        }
        h1 { text-align: left; }
        a:visited { color: inherit; }
        a { text-decoration: none; color: #88f; }
        a:hover, a:focus { text-decoration: underline; outline: none; }
        #logo { height: 2.75rem; padding: 0.25rem 0; }
        span.icon { margin-right: 1rem; }
        @media (prefers-color-scheme: dark) {
            html { background: #111; color: #ccc; }
        }
        """
    )
    EXTRA_STYLE = ""
    TITLE = "Unknown"

    def __init__(self, debug: bool = True) -> None:
        self.doc = Document(self.TITLE, lang="en")
        self.debug = debug

    @property
    def style(self) -> str:
        return self.BASE_STYLE + self.EXTRA_STYLE

    def render(self) -> str:
        self._head()
        self._body()
        return str(self.doc)

    def _head(self) -> None:
        self.doc.style(HTML(self.style))
        with self.doc.header:
            with self.doc.div(class_="container"):
                if self.debug:
                    self.doc(HTML(SVG_LOGO))
                self.doc.div(self.TITLE, id="hdrtext")
                if self.debug:
                    self.doc.div(f"Version {VERSION}", id="hdrver")

    @abstractmethod
    def _body(self) -> None:
        ...
