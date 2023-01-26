from textwrap import dedent
from typing import Iterable, TypedDict

from html5tagger import E

from .base import BasePage


class FileInfo(TypedDict):
    icon: str
    file_name: str
    file_access: str
    file_size: str


class AutoIndex(BasePage):
    EXTRA_STYLE = dedent(
        """
        table.autoindex tr { display: flex; }
        table.autoindex td { margin: 0 0.5rem; }
        table.autoindex td:first-child { flex: 1; }
        table.autoindex td:nth-child(2) { text-align: right; }
        table.autoindex td:last-child {  text-align: right; }
        """
    )
    TITLE = "📁 File browser"

    def __init__(self, files: Iterable[FileInfo]) -> None:
        super().__init__()
        self.files = files

    def _body(self) -> None:
        with self.doc.main:
            self._headline()
            self._file_table(self.files)

    def _headline(self):
        self.doc.h1(self.TITLE)

    def _file_table(self, files: Iterable[FileInfo]):
        with self.doc.table(class_="autoindex"):
            self._parent()
            for f in files:
                self._file_row(**f)

    def _parent(self):
        self._file_row("📁", "..", "", "")

    def _file_row(
        self,
        icon: str,
        file_name: str,
        file_access: str,
        file_size: str,
    ):
        first = E.span(icon, class_="icon").a(file_name, href=file_name)
        self.doc.tr.td(first).td(file_size).td(file_access)
