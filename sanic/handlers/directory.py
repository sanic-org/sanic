from __future__ import annotations

from datetime import datetime
from operator import itemgetter
from pathlib import Path
from stat import S_ISDIR
from typing import Any, Coroutine, Dict, Iterable, Optional, Union, cast

from sanic.exceptions import SanicIsADirectoryError
from sanic.pages.autoindex import AutoIndex, FileInfo
from sanic.request import Request
from sanic.response import file, html
from sanic.response.types import HTTPResponse


class DirectoryHandler:
    def __init__(
        self, directory: Path, autoindex: bool, index_name: str
    ) -> None:
        self.directory = directory
        self.autoindex = autoindex
        self.index_name = index_name

    def handle(self):
        index_file = self.directory / self.index_name
        if self.autoindex and (not index_file.exists() or not self.index_name):
            return self.index()

        if self.index_name:
            return file(index_file)

    def index(self):
        page = AutoIndex(self._iter_files())
        return html(page.render())

    def _prepare_file(self, path: Path) -> Dict[str, Union[int, str]]:
        stat = path.stat()
        modified = datetime.fromtimestamp(stat.st_mtime)
        is_dir = S_ISDIR(stat.st_mode)
        icon = "📁" if is_dir else "📄"
        file_name = path.name
        if is_dir:
            file_name += "/"
        return {
            "priority": is_dir * -1,
            "file_name": file_name,
            "icon": icon,
            "file_access": modified.isoformat(),
            "file_size": stat.st_size,
        }

    def _iter_files(self) -> Iterable[FileInfo]:
        prepared = [self._prepare_file(f) for f in self.directory.iterdir()]
        for item in sorted(prepared, key=itemgetter("priority")):
            del item["priority"]
            yield cast(FileInfo, item)

    @classmethod
    def default_handler(
        cls, request: Request, exception: SanicIsADirectoryError
    ) -> Optional[Coroutine[Any, Any, HTTPResponse]]:
        if exception.autoindex or exception.index_name:
            maybe_response = DirectoryHandler(
                exception.location, exception.autoindex, exception.index_name
            ).handle()
            if maybe_response:
                return maybe_response
        return None
