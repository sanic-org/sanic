from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime
from operator import itemgetter
from pathlib import Path
from stat import S_ISDIR
from typing import cast
from urllib.parse import unquote

from sanic.exceptions import NotFound
from sanic.pages.directory_page import DirectoryPage, FileInfo
from sanic.request import Request
from sanic.response import file, html, redirect


def _is_path_within_root(path: Path, root: Path) -> bool:
    """Check if a path (after resolution) is within the root directory.

    Returns False for:
    - Broken symlinks (cannot be resolved)
    - Paths that resolve outside the root directory
    - Any errors during resolution
    """
    try:
        resolved = path.resolve()
        resolved.relative_to(root.resolve())
    except (ValueError, OSError, RuntimeError):
        return False
    else:
        return True


class DirectoryHandler:
    """Serve files from a directory.

    Args:
        uri (str): The URI to serve the files at.
        directory (Path): The directory to serve files from.
        directory_view (bool): Whether to show a directory listing or not.
        index (str | Sequence[str] | None): The index file(s) to
            serve if the directory is requested. Defaults to None.
        root_path (Optional[Path]): The root path for security checks.
            Symlinks resolving outside this path will be hidden from
            directory listings. Defaults to directory if not specified.
        follow_external_symlink_files (bool): Whether to show file symlinks
            pointing outside root in directory listings. Defaults to False.
        follow_external_symlink_dirs (bool): Whether to show directory symlinks
            pointing outside root in directory listings. Defaults to False.
    """

    def __init__(
        self,
        uri: str,
        directory: Path,
        directory_view: bool = False,
        index: str | Sequence[str] | None = None,
        root_path: Path | None = None,
        follow_external_symlink_files: bool = False,
        follow_external_symlink_dirs: bool = False,
    ) -> None:
        if isinstance(index, str):
            index = [index]
        elif index is None:
            index = []
        self.base = uri.strip("/")
        self.directory = directory
        self.directory_view = directory_view
        self.index = tuple(index)
        self.root_path = root_path if root_path is not None else directory
        self.follow_external_symlink_files = follow_external_symlink_files
        self.follow_external_symlink_dirs = follow_external_symlink_dirs

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
        current = unquote(path).strip("/")[len(self.base) :].strip("/")  # noqa: E203
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

    def _prepare_file(self, path: Path) -> dict[str, int | str] | None:
        try:
            stat = path.stat()
        except OSError:
            return None
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
        prepared = []
        for f in location.iterdir():
            if f.is_symlink() and not _is_path_within_root(f, self.root_path):
                # External symlink - check if allowed based on type
                try:
                    is_dir = f.resolve().is_dir()
                except OSError:
                    continue  # Broken symlink
                if is_dir and not self.follow_external_symlink_dirs:
                    continue
                if not is_dir and not self.follow_external_symlink_files:
                    continue
            file_info = self._prepare_file(f)
            if file_info is not None:
                prepared.append(file_info)
        for item in sorted(prepared, key=itemgetter("priority", "file_name")):
            del item["priority"]
            yield cast(FileInfo, item)
