from __future__ import annotations

from datetime import datetime
from operator import itemgetter
from pathlib import Path
from stat import S_ISDIR
from typing import Dict, Iterable, Sequence, Union, cast

from sanic.exceptions import NotFound
from sanic.pages.autoindex import AutoIndex, FileInfo
from sanic.request import Request
from sanic.response import file, html, redirect


class DirectoryHandler:
    def __init__(self, debug: bool) -> None:
        self.debug = debug

    async def handle(
        self,
        request: Request,
        directory: Path,
        autoindex: bool,
        index: Sequence[str],
        url: str,
    ):
        for file_name in index:
            index_file = directory / file_name
            if index_file.is_file():
                return await file(index_file)

        if autoindex:
            return self.index(directory, url)

        raise NotFound(f"{str(directory)} is not found")

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
