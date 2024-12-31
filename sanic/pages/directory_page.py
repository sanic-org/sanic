from collections.abc import Iterable
from typing import TypedDict

from html5tagger import E

from .base import BasePage


class FileInfo(TypedDict):
    """Type for file info."""

    icon: str
    file_name: str
    file_access: str
    file_size: str


class DirectoryPage(BasePage):  # no cov
    """Page for viewing a directory."""

    TITLE = "Directory Viewer"

    def __init__(
        self, files: Iterable[FileInfo], url: str, debug: bool
    ) -> None:
        super().__init__(debug)
        self.files = files
        self.url = url

    def _body(self) -> None:
        with self.doc.main:
            self._headline()
            files = list(self.files)
            if files:
                self._file_table(files)
            else:
                self.doc.p("The folder is empty.")

    def _headline(self):
        """Implement a heading with the current path, combined with
        breadcrumb links"""
        with self.doc.h1(id="breadcrumbs"):
            p = self.url.split("/")[:-1]

            for i, part in enumerate(p):
                path = "/".join(p[: i + 1]) + "/"
                with self.doc.a(href=path):
                    self.doc.span(part, class_="dir").span("/", class_="sep")

    def _file_table(self, files: Iterable[FileInfo]):
        with self.doc.table(class_="autoindex container"):
            for f in files:
                self._file_row(**f)

    def _file_row(
        self,
        icon: str,
        file_name: str,
        file_access: str,
        file_size: str,
    ):
        first = E.span(icon, class_="icon").a(file_name, href=file_name)
        self.doc.tr.td(first).td(file_size).td(file_access)
