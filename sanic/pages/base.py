from abc import ABC, abstractmethod
from textwrap import dedent
from sanic import __version__ as VERSION

from html5tagger import Document, HTML


LOGO_SVG = HTML("""<svg id=logo alt=Sanic viewBox="0 0 964 279"><path d="M107 222c9-2 10-20 1-22s-20-2-30-2-17 7-16 14 6 10 15 10h30zm115-1c16-2 30-11 35-23s6-24 2-33-6-14-15-20-24-11-38-10c-7 3-10 13-5 19s17-1 24 4 15 14 13 24-5 15-14 18-50 0-74 0h-17c-6 4-10 15-4 20s16 2 23 3zM251 83q9-1 9-7 0-15-10-16h-13c-10 6-10 20 0 22zM147 60c-4 0-10 3-11 11s5 13 10 12 42 0 67 0c5-3 7-10 6-15s-4-8-9-8zm-33 1c-8 0-16 0-24 3s-20 10-25 20-6 24-4 36 15 22 26 27 78 8 94 3c4-4 4-12 0-18s-69 8-93-10c-8-7-9-23 0-30s12-10 20-10 12 2 16-3 1-15-5-18z" fill="#ff0d68"/><path d="M676 74c0-14-18-9-20 0s0 30 0 39 20 9 20 2zm-297-10c-12 2-15 12-23 23l-41 58H340l22-30c8-12 23-13 30-4s20 24 24 38-10 10-17 10l-68 2q-17 1-48 30c-7 6-10 20 0 24s15-8 20-13 20 -20 58-21h50 c20 2 33 9 52 30 8 10 24-4 16-13L384 65q-3-2-5-1zm131 0c-10 1-12 12-11 20v96c1 10-3 23 5 32s20-5 17-15c0-23-3-46 2-67 5-12 22-14 32-5l103 87c7 5 19 1 18-9v-64c-3-10-20-9-21 2s-20 22-30 13l-97-80c-5-4-10-10-18-10zM701 76v128c2 10 15 12 20 4s0-102 0-124s-20-18-20-7z    M850 63c-35 0-69-2-86 15s-20 60-13 66 13 8 16 0 1-10 1-27 12-26 20-32 66-5 85-5 31 4 31-10-18-7-54-7M764 159c-6-2-15-2-16 12s19 37 33 43 23 8 25-4-4-11-11-14q-9-3-22-18c-4-7-3-16-10-19zM828 196c-4 0-8 1-10 5s-4 12 0 15 8 2 12 2h60c5 0 10-2 12-6 3-7-1-16-8-16z" fill="#e1e1e1"/></svg>""")

class BasePage(ABC):
    BASE_STYLE = dedent(
        """
        body { margin: 0; font: 1.2rem sans-serif; }
        body > * { padding: 0 2rem; }
        header {
            display: flex; align-items: center; justify-content: space-between;
            background: #555; color: #e1e1e1;
        }
        a:visited { color: inherit; }
        a { text-decoration: none; color: #88f; }
        a:hover, a:focus { text-decoration: underline; outline: none; }
        #logo { height: 2.5rem; }
        table { width: 100%; max-width: 1200px; }
        span.icon { margin-right: 1rem; }
        @media (prefers-color-scheme: dark) {
            html { background: #111; color: #ccc; }
        }
        """
    )
    EXTRA_STYLE = ""
    TITLE = "Unknown"

    def __init__(self) -> None:
        self.doc = Document(self.TITLE, lang="en")

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
            self.doc(LOGO_SVG).div(self.TITLE, id="hdrtext").div(f"Version {VERSION}", id="hdrver")

    @abstractmethod
    def _body(self) -> None:
        ...


class ErrorPage(BasePage):
    TITLE = "Error while handling your request"

    def __init__(self, title: str, text: str, exc: Exception, full: bool) -> None:
        super().__init__()
        self.title = title
        self.text = text
        self.exc = exc
        self.full = full

    def _body(self) -> None:
        with self.doc.main:
            self.doc.h1(f"⚠️ {self.title}")
            if self.full and self.exc:
                from niceback import html_traceback
                self.doc(html_traceback(self.exc))
            else:
                self.doc.p(self.text)

