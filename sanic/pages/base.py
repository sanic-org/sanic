from abc import ABC, abstractmethod
from textwrap import dedent

from html5tagger import Document


class BasePage(ABC):
    BASE_STYLE = dedent(
        """
        html { font-family: sans-serif; }
        main { padding: 1rem; }
        table { width: 100%; max-width: 1200px; }
        td { font-family: monospace; }
        span.icon { margin-right: 1rem; }
        @media (prefers-color-scheme: dark) {
            html { background: #111; color: #ccc; }
            a { color: #ccc; }
            a:visited { color: #777; }
        }
        """
    )
    EXTRA_STYLE = ""
    TITLE = "Unknown"

    def __init__(self) -> None:
        self.doc = Document(title=self.TITLE, lang="en")

    @property
    def style(self) -> str:
        return self.BASE_STYLE + self.EXTRA_STYLE

    def render(self) -> str:
        self._head()
        self._body()
        return str(self.doc)

    def _head(self) -> None:
        self.doc.head.title(self.TITLE).style(self.style)

    @abstractmethod
    def _body(self) -> None:
        ...
