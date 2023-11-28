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
    """Serve files from a directory.

    Args:
        uri (str): The URI to serve the files at.
        directory (Path): The directory to serve files from.
        directory_view (bool): Whether to show a directory listing or not.
        index (Optional[Union[str, Sequence[str]]]): The index file(s) to
            serve if the directory is requested. Defaults to None.
    """

    def __init__(
        self,
        uri: str,
        directory: Path,
        directory_view: bool = False,
        index: Optional[Union[str, Sequence[str]]] = None,
    ) -> None:
        if isinstance(index, str):
            index = [index]
        elif index is None:
            index = []
        self.base = uri.strip("/")
        self.directory = directory
        self.directory_view = directory_view
        self.index = tuple(index)

    async def handle(self, request: Request, path: str):
        """Handle the request.

        Args:
            request (Request): The incoming request object.
            path (str): The path to the file to serve.

        Raises:
            NotFound: If the file is not found.
            IsADirectoryError: If the path is a directory and directory_view is False.

        Returns:
            Response: The response object.
        """  # noqa: E501
        current = path.strip("/")[len(self.base) :].strip("/")  # noqa: E203
        for file_name in self.index:
            index_file = self.directory / current / file_name
            if index_file.is_file():
                return await file(index_file)

        if self.directory_view:
            return self._index(
                self.directory / current, path, request.app.debug
            )

        if self.index:
            raise NotFound("File not found")

        raise IsADirectoryError(f"{self.directory.as_posix()} is a directory")

    def _index(self, location: Path, path: str, debug: bool):
        # Remove empty path elements, append slash
        if "//" in path or not path.endswith("/"):
            return redirect(
                "/" + "".join([f"{p}/" for p in path.split("/") if p])
            )

        # Render file browser
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
