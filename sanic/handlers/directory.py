from __future__ import annotations

from datetime import datetime
from operator import itemgetter
from pathlib import Path
from stat import S_ISDIR
from typing import Any, Coroutine, Dict, Iterable, Optional, Union, cast

from sanic.exceptions import SanicIsADirectoryError
from sanic.pages.autoindex import AutoIndex, FileInfo
from sanic.request import Request
from sanic.response import file, html, redirect
from sanic.response.types import HTTPResponse


class DirectoryHandler:
    def __init__(self, debug: bool) -> None:
        self.debug = debug

    def handle(
        self, directory: Path, autoindex: bool, index_name: str, url: str
    ):
        index_file = directory / index_name
        if autoindex and (not index_file.exists() or not index_name):
            return self.index(directory, url)

        if index_name:
            return file(index_file)

    def index(self, directory: Path, url: str):
        # Remove empty path elements, append slash
        if "//" in url or not url.endswith("/"):
            return redirect(
                "/" + "".join([f"{p}/" for p in url.split("/") if p])
            )
        # Render file browser
        page = AutoIndex(self._iter_files(directory), url, self.debug)
        return html(page.render())

    def _prepare_file(self, path: Path) -> Dict[str, Union[int, str]]:
        stat = path.stat()
        modified = (
            datetime.fromtimestamp(stat.st_mtime)
            .isoformat()[:19]
            .replace("T", " ")
        )
        is_dir = S_ISDIR(stat.st_mode)
        icon = "📁" if is_dir else "📄"
        file_name = path.name
        if is_dir:
            file_name += "/"
        return {
            "priority": is_dir * -1,
            "file_name": file_name,
            "icon": icon,
            "file_access": modified,
            "file_size": stat.st_size,
        }

    def _iter_files(self, directory: Path) -> Iterable[FileInfo]:
        prepared = [self._prepare_file(f) for f in directory.iterdir()]
        for item in sorted(prepared, key=itemgetter("priority", "file_name")):
            del item["priority"]
            yield cast(FileInfo, item)

    @classmethod
    def default_handler(
        cls, request: Request, exception: SanicIsADirectoryError
    ) -> Optional[Coroutine[Any, Any, HTTPResponse]]:
        if exception.autoindex or exception.index_name:
            maybe_response = request.app.directory_handler.handle(
                exception.location,
                exception.autoindex,
                exception.index_name,
                request.path,
            )
            if maybe_response:
                return maybe_response
        return None
