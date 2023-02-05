from __future__ import annotations

from datetime import datetime
from operator import itemgetter
from pathlib import Path
from stat import S_ISDIR
from typing import Dict, Iterable, Optional, Sequence, Union, cast

from sanic.exceptions import NotFound
from sanic.pages.directory_page import DirectoryPage, FileInfo
from sanic.request import Request
from sanic.response import file, html, redirect


class DirectoryHandler:
    def __init__(
        self,
        uri: str,
        directory: Path,
        directory_view: bool = False,
        directory_index: Optional[Union[str, Sequence[str]]] = None,
    ) -> None:
        if isinstance(directory_index, str):
            directory_index = [directory_index]
        elif directory_index is None:
            directory_index = []
        self.base = uri.strip("/")
        self.directory = directory
        self.directory_view = directory_view
        self.directory_index = tuple(directory_index)

    async def handle(self, request: Request, path: str):
        for file_name in self.directory_index:
            index_file = self.directory / file_name
            if index_file.is_file():
                return await file(index_file)

        if self.directory_view:
            return self.index(path, request.app.debug)

        raise NotFound(f"{self.directory.as_posix()} is not found")

    def index(self, path: str, debug: bool):
        # Remove empty path elements, append slash
        if "//" in path or not path.endswith("/"):
            return redirect(
                "/" + "".join([f"{p}/" for p in path.split("/") if p])
            )
        # Render file browser
        current = path.strip("/")[len(self.base) :]  # noqa: E203
        location = self.directory / current.strip("/")
        page = DirectoryPage(self._iter_files(location), path, debug)
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

    def _iter_files(self, location: Path) -> Iterable[FileInfo]:
        prepared = [self._prepare_file(f) for f in location.iterdir()]
        for item in sorted(prepared, key=itemgetter("priority", "file_name")):
            del item["priority"]
            yield cast(FileInfo, item)
