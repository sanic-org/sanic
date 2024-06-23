from email.utils import formatdate
from functools import partial, wraps
from mimetypes import guess_type
from os import PathLike, path
from pathlib import Path, PurePath
from typing import Optional, Sequence, Set, Union
from urllib.parse import unquote

from sanic_routing.route import Route

from sanic.base.meta import SanicMeta
from sanic.compat import stat_async
from sanic.constants import DEFAULT_HTTP_CONTENT_TYPE
from sanic.exceptions import FileNotFound, HeaderNotFound, RangeNotSatisfiable
from sanic.handlers import ContentRangeHandler
from sanic.handlers.directory import DirectoryHandler
from sanic.log import error_logger
from sanic.mixins.base import BaseMixin
from sanic.models.futures import FutureStatic
from sanic.request import Request
from sanic.response import HTTPResponse, file, file_stream, validate_file


class StaticMixin(BaseMixin, metaclass=SanicMeta):
    def __init__(self, *args, **kwargs) -> None:
        self._future_statics: Set[FutureStatic] = set()

    def _apply_static(self, static: FutureStatic) -> Route:
        raise NotImplementedError  # noqa

    def static(
        self,
        uri: str,
        file_or_directory: Union[PathLike, str],
        pattern: str = r"/?.+",
        use_modified_since: bool = True,
        use_content_range: bool = False,
        stream_large_files: Union[bool, int] = False,
        name: str = "static",
        host: Optional[str] = None,
        strict_slashes: Optional[bool] = None,
        content_type: Optional[str] = None,
        apply: bool = True,
        resource_type: Optional[str] = None,
        index: Optional[Union[str, Sequence[str]]] = None,
        directory_view: bool = False,
        directory_handler: Optional[DirectoryHandler] = None,
    ):
        """Register a root to serve files from. The input can either be a file or a directory.

        This method provides an easy and simple way to set up the route necessary to serve static files.

        Args:
            uri (str): URL path to be used for serving static content.
            file_or_directory (Union[PathLike, str]): Path to the static file
                or directory with static files.
            pattern (str, optional): Regex pattern identifying the valid
                static files. Defaults to `r"/?.+"`.
            use_modified_since (bool, optional): If true, send file modified
                time, and return not modified if the browser's matches the
                server's. Defaults to `True`.
            use_content_range (bool, optional): If true, process header for
                range requests and sends  the file part that is requested.
                Defaults to `False`.
            stream_large_files (Union[bool, int], optional): If `True`, use
                the `StreamingHTTPResponse.file_stream` handler rather than
                the `HTTPResponse.file handler` to send the file. If this
                is an integer, it represents the threshold size to switch
                to `StreamingHTTPResponse.file_stream`. Defaults to `False`,
                which means that the response will not be streamed.
            name (str, optional): User-defined name used for url_for.
                Defaults to `"static"`.
            host (Optional[str], optional): Host IP or FQDN for the
                service to use.
            strict_slashes (Optional[bool], optional): Instruct Sanic to
                check if the request URLs need to terminate with a slash.
            content_type (Optional[str], optional): User-defined content type
                for header.
            apply (bool, optional): If true, will register the route
                immediately. Defaults to `True`.
            resource_type (Optional[str], optional): Explicitly declare a
                resource to be a `"file"` or a `"dir"`.
            index (Optional[Union[str, Sequence[str]]], optional): When
                exposing against a directory, index is  the name that will
                be served as the default file. When multiple file names are
                passed, then they will be tried in order.
            directory_view (bool, optional): Whether to fallback to showing
                the directory viewer when exposing a directory. Defaults
                to `False`.
            directory_handler (Optional[DirectoryHandler], optional): An
                instance of DirectoryHandler that can be used for explicitly
                controlling and subclassing the behavior of the default
                directory handler.

        Returns:
            List[sanic.router.Route]: Routes registered on the router.

        Examples:
            Serving a single file:
            ```python
            app.static('/foo', 'path/to/static/file.txt')
            ```

            Serving all files from a directory:
            ```python
            app.static('/static', 'path/to/static/directory')
            ```

            Serving large files with a specific threshold:
            ```python
            app.static('/static', 'path/to/large/files', stream_large_files=1000000)
            ```
        """  # noqa: E501

        name = self.generate_name(name)

        if strict_slashes is None and self.strict_slashes is not None:
            strict_slashes = self.strict_slashes

        if not isinstance(file_or_directory, (str, bytes, PurePath)):
            raise ValueError(
                f"Static route must be a valid path, not {file_or_directory}"
            )

        try:
            file_or_directory = Path(file_or_directory).resolve()
        except TypeError:
            raise TypeError(
                "Static file or directory must be a path-like object or string"
            )

        if directory_handler and (directory_view or index):
            raise ValueError(
                "When explicitly setting directory_handler, you cannot "
                "set either directory_view or index. Instead, pass "
                "these arguments to your DirectoryHandler instance."
            )

        if not directory_handler:
            directory_handler = DirectoryHandler(
                uri=uri,
                directory=file_or_directory,
                directory_view=directory_view,
                index=index,
            )

        static = FutureStatic(
            uri,
            file_or_directory,
            pattern,
            use_modified_since,
            use_content_range,
            stream_large_files,
            name,
            host,
            strict_slashes,
            content_type,
            resource_type,
            directory_handler,
        )
        self._future_statics.add(static)

        if apply:
            self._apply_static(static)


class StaticHandleMixin(metaclass=SanicMeta):
    def _apply_static(self, static: FutureStatic) -> Route:
        return self._register_static(static)

    def _register_static(
        self,
        static: FutureStatic,
    ):
        # TODO: Though sanic is not a file server, I feel like we should
        # at least make a good effort here.  Modified-since is nice, but
        # we could also look into etags, expires, and caching
        """
        Register a static directory handler with Sanic by adding a route to the
        router and registering a handler.
        """

        if isinstance(static.file_or_directory, bytes):
            file_or_directory = static.file_or_directory.decode("utf-8")
        elif isinstance(static.file_or_directory, PurePath):
            file_or_directory = str(static.file_or_directory)
        elif not isinstance(static.file_or_directory, str):
            raise ValueError("Invalid file path string.")
        else:
            file_or_directory = static.file_or_directory

        uri = static.uri
        name = static.name
        # If we're not trying to match a file directly,
        # serve from the folder
        if not static.resource_type:
            if not path.isfile(file_or_directory):
                uri = uri.rstrip("/")
                uri += "/<__file_uri__:path>"
        elif static.resource_type == "dir":
            if path.isfile(file_or_directory):
                raise TypeError(
                    "Resource type improperly identified as directory. "
                    f"'{file_or_directory}'"
                )
            uri = uri.rstrip("/")
            uri += "/<__file_uri__:path>"
        elif static.resource_type == "file" and not path.isfile(
            file_or_directory
        ):
            raise TypeError(
                "Resource type improperly identified as file. "
                f"'{file_or_directory}'"
            )
        elif static.resource_type != "file":
            raise ValueError(
                "The resource_type should be set to 'file' or 'dir'"
            )

        # special prefix for static files
        # if not static.name.startswith("_static_"):
        #     name = f"_static_{static.name}"

        _handler = wraps(self._static_request_handler)(
            partial(
                self._static_request_handler,
                file_or_directory=file_or_directory,
                use_modified_since=static.use_modified_since,
                use_content_range=static.use_content_range,
                stream_large_files=static.stream_large_files,
                content_type=static.content_type,
                directory_handler=static.directory_handler,
            )
        )

        route, _ = self.route(  # type: ignore
            uri=uri,
            methods=["GET", "HEAD"],
            name=name,
            host=static.host,
            strict_slashes=static.strict_slashes,
            static=True,
        )(_handler)

        return route

    async def _static_request_handler(
        self,
        request: Request,
        *,
        file_or_directory: PathLike,
        use_modified_since: bool,
        use_content_range: bool,
        stream_large_files: Union[bool, int],
        directory_handler: DirectoryHandler,
        content_type: Optional[str] = None,
        __file_uri__: Optional[str] = None,
    ):
        not_found = FileNotFound(
            "File not found",
            path=file_or_directory,
            relative_url=__file_uri__,
        )

        # Merge served directory and requested file if provided
        file_path = await self._get_file_path(
            file_or_directory, __file_uri__, not_found
        )

        try:
            headers = {}
            # Check if the client has been sent this file before
            # and it has not been modified since
            stats = None
            if use_modified_since:
                stats = await stat_async(file_path)
                modified_since = stats.st_mtime
                response = await validate_file(request.headers, modified_since)
                if response:
                    return response
                headers["Last-Modified"] = formatdate(
                    modified_since, usegmt=True
                )
            _range = None
            if use_content_range:
                _range = None
                if not stats:
                    stats = await stat_async(file_path)
                headers["Accept-Ranges"] = "bytes"
                headers["Content-Length"] = str(stats.st_size)
                if request.method != "HEAD":
                    try:
                        _range = ContentRangeHandler(request, stats)
                    except HeaderNotFound:
                        pass
                    else:
                        del headers["Content-Length"]
                        headers.update(_range.headers)

            if "content-type" not in headers:
                content_type = (
                    content_type
                    or guess_type(file_path)[0]
                    or DEFAULT_HTTP_CONTENT_TYPE
                )

                if "charset=" not in content_type and (
                    content_type.startswith("text/")
                    or content_type == "application/javascript"
                ):
                    content_type += "; charset=utf-8"

                headers["Content-Type"] = content_type

            if request.method == "HEAD":
                return HTTPResponse(headers=headers)
            else:
                if stream_large_files:
                    if isinstance(stream_large_files, bool):
                        threshold = 1024 * 1024
                    else:
                        threshold = stream_large_files

                    if not stats:
                        stats = await stat_async(file_path)
                    if stats.st_size >= threshold:
                        return await file_stream(
                            file_path, headers=headers, _range=_range
                        )
                return await file(file_path, headers=headers, _range=_range)
        except (IsADirectoryError, PermissionError):
            return await directory_handler.handle(request, request.path)
        except RangeNotSatisfiable:
            raise
        except FileNotFoundError:
            raise not_found
        except Exception:
            error_logger.exception(
                "Exception in static request handler: "
                f"path={file_or_directory}, "
                f"relative_url={__file_uri__}"
            )
            raise

    async def _get_file_path(self, file_or_directory, __file_uri__, not_found):
        file_path_raw = Path(unquote(file_or_directory))
        root_path = file_path = file_path_raw.resolve()

        if __file_uri__:
            # Strip all / that in the beginning of the URL to help prevent
            # python from herping a derp and treating the uri as an
            # absolute path
            unquoted_file_uri = unquote(__file_uri__).lstrip("/")
            file_path_raw = Path(file_or_directory, unquoted_file_uri)
            file_path = file_path_raw.resolve()
            if (
                file_path < root_path and not file_path_raw.is_symlink()
            ) or ".." in file_path_raw.parts:
                error_logger.exception(
                    f"File not found: path={file_or_directory}, "
                    f"relative_url={__file_uri__}"
                )
                raise not_found

        try:
            file_path.relative_to(root_path)
        except ValueError:
            if not file_path_raw.is_symlink():
                error_logger.exception(
                    f"File not found: path={file_or_directory}, "
                    f"relative_url={__file_uri__}"
                )
                raise not_found
        return file_path
