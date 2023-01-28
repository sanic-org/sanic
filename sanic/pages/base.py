from abc import ABC, abstractmethod
from textwrap import dedent

from html5tagger import HTML, Document

from sanic import __version__ as VERSION
from sanic.application.logo import SVG_LOGO


class BasePage(ABC):
    BASE_STYLE = dedent(
        """
        body { margin: 0; font: 16px sans-serif; }
        body > * { padding: 0 2rem; }
        header {
            display: flex; align-items: center; justify-content: space-between;
            background: #111; color: #e1e1e1; border-bottom: 1px solid #272727;
        }
        main { padding-bottom: 3rem; }
        h2 { margin: 2rem 0 1rem 0; }
        a:visited { color: inherit; }
        a { text-decoration: none; color: #88f; }
        a:hover, a:focus { text-decoration: underline; outline: none; }
        #logo { height: 2.5rem; }
        table { width: 100%; max-width: 1200px; word-break: break-all; }
        #logo { height: 2.75rem; padding: 0.25rem 0; }
        .smalltext { font-size: 1rem; }
        .nobr { white-space: nowrap; }
        table { width: 100%; max-width: 1200px; }
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
        if self.debug:
            with self.doc.header:
                self.doc(HTML(SVG_LOGO)).div(self.TITLE, id="hdrtext").div(
                    f"Version {VERSION}", id="hdrver"
                )

    @abstractmethod
    def _body(self) -> None:
        ...
