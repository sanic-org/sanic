from __future__ import annotations

from datetime import datetime, timezone
from email.utils import formatdate, parsedate_to_datetime
from mimetypes import guess_type
from operator import itemgetter
from os import path
from pathlib import Path, PurePath
from stat import S_ISDIR
from time import time
from typing import Any, AnyStr, Callable, Dict, Optional, Tuple, Union
from urllib.parse import quote_plus

from sanic.compat import Header, open_async, stat_async
from sanic.constants import DEFAULT_HTTP_CONTENT_TYPE
from sanic.helpers import Default, _default
from sanic.log import logger
from sanic.models.protocol_types import HTMLProtocol, Range

from .types import HTTPResponse, JSONResponse, ResponseStream


def empty(
    status: int = 204, headers: Optional[Dict[str, str]] = None
) -> HTTPResponse:
    """
    Returns an empty response to the client.

    :param status Response code.
    :param headers Custom Headers.
    """
    return HTTPResponse(body=b"", status=status, headers=headers)


def json(
    body: Any,
    status: int = 200,
    headers: Optional[Dict[str, str]] = None,
    content_type: str = "application/json",
    dumps: Optional[Callable[..., str]] = None,
    **kwargs: Any,
) -> JSONResponse:
    """
    Returns response object with body in json format.

    :param body: Response data to be serialized.
    :param status: Response code.
    :param headers: Custom Headers.
    :param kwargs: Remaining arguments that are passed to the json encoder.
    """

    return JSONResponse(
        body,
        status=status,
        headers=headers,
        content_type=content_type,
        dumps=dumps,
        **kwargs,
    )


def text(
    body: str,
    status: int = 200,
    headers: Optional[Dict[str, str]] = None,
    content_type: str = "text/plain; charset=utf-8",
) -> HTTPResponse:
    """
    Returns response object with body in text format.

    :param body: Response data to be encoded.
    :param status: Response code.
    :param headers: Custom Headers.
    :param content_type: the content type (string) of the response
    """
    if not isinstance(body, str):
        raise TypeError(
            f"Bad body type. Expected str, got {type(body).__name__})"
        )

    return HTTPResponse(
        body, status=status, headers=headers, content_type=content_type
    )


def raw(
    body: Optional[AnyStr],
    status: int = 200,
    headers: Optional[Dict[str, str]] = None,
    content_type: str = DEFAULT_HTTP_CONTENT_TYPE,
) -> HTTPResponse:
    """
    Returns response object without encoding the body.

    :param body: Response data.
    :param status: Response code.
    :param headers: Custom Headers.
    :param content_type: the content type (string) of the response.
    """
    return HTTPResponse(
        body=body,
        status=status,
        headers=headers,
        content_type=content_type,
    )


def html(
    body: Union[str, bytes, HTMLProtocol],
    status: int = 200,
    headers: Optional[Dict[str, str]] = None,
) -> HTTPResponse:
    """
    Returns response object with body in html format.

    :param body: str or bytes-ish, or an object with __html__ or _repr_html_.
    :param status: Response code.
    :param headers: Custom Headers.
    """
    if not isinstance(body, (str, bytes)):
        if hasattr(body, "__html__"):
            body = body.__html__()
        elif hasattr(body, "_repr_html_"):
            body = body._repr_html_()

    return HTTPResponse(  # type: ignore
        body,
        status=status,
        headers=headers,
        content_type="text/html; charset=utf-8",
    )


async def validate_file(
    request_headers: Header, last_modified: Union[datetime, float, int]
):
    try:
        if_modified_since = request_headers.getone("If-Modified-Since")
    except KeyError:
        return
    try:
        if_modified_since = parsedate_to_datetime(if_modified_since)
    except (TypeError, ValueError):
        logger.warning(
            "Ignorning invalid If-Modified-Since header received: " "'%s'",
            if_modified_since,
        )
        return
    if not isinstance(last_modified, datetime):
        last_modified = datetime.fromtimestamp(
            float(last_modified), tz=timezone.utc
        ).replace(microsecond=0)
    if last_modified <= if_modified_since:
        return HTTPResponse(status=304)


async def file(
    location: Union[str, PurePath],
    status: int = 200,
    request_headers: Optional[Header] = None,
    validate_when_requested: bool = True,
    mime_type: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    filename: Optional[str] = None,
    last_modified: Optional[Union[datetime, float, int, Default]] = _default,
    max_age: Optional[Union[float, int]] = None,
    no_store: Optional[bool] = None,
    _range: Optional[Range] = None,
    autoindex: bool = False,
    index_name: str = "",
) -> HTTPResponse:
    """Return a response object with file data.
    :param status: HTTP response code. Won't enforce the passed in
        status if only a part of the content will be sent (206)
        or file is being validated (304).
    :param request_headers: The request headers.
    :param validate_when_requested: If True, will validate the
        file when requested.
    :param location: Location of file on system.
    :param mime_type: Specific mime_type.
    :param headers: Custom Headers.
    :param filename: Override filename.
    :param last_modified: The last modified date and time of the file.
    :param max_age: Max age for cache control.
    :param no_store: Any cache should not store this response.
    :param _range:
    """

    if isinstance(last_modified, datetime):
        last_modified = last_modified.replace(microsecond=0).timestamp()
    elif isinstance(last_modified, Default):
        stat = await stat_async(location)
        last_modified = stat.st_mtime

    if (
        validate_when_requested
        and request_headers is not None
        and last_modified
    ):
        response = await validate_file(request_headers, last_modified)
        if response:
            return response

    headers = headers or {}
    if last_modified:
        headers.setdefault(
            "Last-Modified", formatdate(last_modified, usegmt=True)
        )

    if filename:
        headers.setdefault(
            "Content-Disposition", f'attachment; filename="{filename}"'
        )

    if no_store:
        cache_control = "no-store"
    elif max_age:
        cache_control = f"public, max-age={max_age}"
        headers.setdefault(
            "expires",
            formatdate(
                time() + max_age,
                usegmt=True,
            ),
        )
    else:
        cache_control = "no-cache"

    headers.setdefault("cache-control", cache_control)

    filename = filename or path.split(location)[-1]

    try:
        async with await open_async(location, mode="rb") as f:
            if _range:
                await f.seek(_range.start)
                out_stream = await f.read(_range.size)
                headers[
                    "Content-Range"
                ] = f"bytes {_range.start}-{_range.end}/{_range.total}"
                status = 206
            else:
                out_stream = await f.read()
    except IsADirectoryError:
        if autoindex or index_name:
            maybe_response = await AutoIndex(
                Path(location), autoindex, index_name
            ).handle()
            if maybe_response:
                return maybe_response
        raise

    mime_type = mime_type or guess_type(filename)[0] or "text/plain"
    return HTTPResponse(
        body=out_stream,
        status=status,
        headers=headers,
        content_type=mime_type,
    )


def redirect(
    to: str,
    headers: Optional[Dict[str, str]] = None,
    status: int = 302,
    content_type: str = "text/html; charset=utf-8",
) -> HTTPResponse:
    """
    Abort execution and cause a 302 redirect (by default) by setting a
    Location header.

    :param to: path or fully qualified URL to redirect to
    :param headers: optional dict of headers to include in the new request
    :param status: status code (int) of the new request, defaults to 302
    :param content_type: the content type (string) of the response
    """
    headers = headers or {}

    # URL Quote the URL before redirecting
    safe_to = quote_plus(to, safe=":/%#?&=@[]!$&'()*+,;")

    # According to RFC 7231, a relative URI is now permitted.
    headers["Location"] = safe_to

    return HTTPResponse(
        status=status, headers=headers, content_type=content_type
    )


async def file_stream(
    location: Union[str, PurePath],
    status: int = 200,
    chunk_size: int = 4096,
    mime_type: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    filename: Optional[str] = None,
    _range: Optional[Range] = None,
) -> ResponseStream:
    """Return a streaming response object with file data.

    :param location: Location of file on system.
    :param chunk_size: The size of each chunk in the stream (in bytes)
    :param mime_type: Specific mime_type.
    :param headers: Custom Headers.
    :param filename: Override filename.
    :param _range:
    """
    headers = headers or {}
    if filename:
        headers.setdefault(
            "Content-Disposition", f'attachment; filename="{filename}"'
        )
    filename = filename or path.split(location)[-1]
    mime_type = mime_type or guess_type(filename)[0] or "text/plain"
    if _range:
        start = _range.start
        end = _range.end
        total = _range.total

        headers["Content-Range"] = f"bytes {start}-{end}/{total}"
        status = 206

    async def _streaming_fn(response):
        async with await open_async(location, mode="rb") as f:
            if _range:
                await f.seek(_range.start)
                to_send = _range.size
                while to_send > 0:
                    content = await f.read(min((_range.size, chunk_size)))
                    if len(content) < 1:
                        break
                    to_send -= len(content)
                    await response.write(content)
            else:
                while True:
                    content = await f.read(chunk_size)
                    if len(content) < 1:
                        break
                    await response.write(content)

    return ResponseStream(
        streaming_fn=_streaming_fn,
        status=status,
        headers=headers,
        content_type=mime_type,
    )


class AutoIndex:
    INDEX_STYLE = """
        html { font-family: sans-serif }
        ul { padding: 0; list-style: none; }
        li {
            display: flex; justify-content: space-between;
            font-family: monospace;
        }
        li > span { padding: 0.1rem 0.6rem; }
        li > span:first-child { flex: 4; }
        li > span:last-child { flex: 1; }
    """
    OUTPUT_HTML = (
        "<!DOCTYPE html><html lang=en>"
        "<meta charset=UTF-8><title>{title}</title>\n"
        "<style>{style}</style>\n"
        "<h1>{title}</h1>\n"
        "{body}"
    )
    FILE_WRAPPER_HTML = "<ul>{first_line}{files}</ul>"
    FILE_LINE_HTML = (
        "<li>"
        "<span>{icon} <a href={file_name}>{file_name}</a></span>"
        "<span>{file_access}</span>"
        "<span>{file_size}</span>"
        "</li>"
    )

    def __init__(
        self, directory: Path, autoindex: bool, index_name: str
    ) -> None:
        self.directory = directory
        self.autoindex = autoindex
        self.index_name = index_name

    async def handle(self):
        index_file = self.directory / self.index_name
        if self.autoindex and (not index_file.exists() or not self.index_name):
            return await self.index()

        if self.index_name:
            return await file(index_file)

    async def index(self):
        return html(
            self.OUTPUT_HTML.format(
                title="📁 File browser",
                style=self.INDEX_STYLE,
                body=self._list_files(),
            )
        )

    def _list_files(self) -> str:
        prepared = [self._prepare_file(f) for f in self.directory.iterdir()]
        files = "".join(itemgetter(2)(p) for p in sorted(prepared))
        return self.FILE_WRAPPER_HTML.format(
            files=files,
            first_line=self.FILE_LINE_HTML.format(
                icon="📁", file_name="..", file_access="", file_size=""
            ),
        )

    def _prepare_file(self, path: Path) -> Tuple[int, str, str]:
        stat = path.stat()
        modified = datetime.fromtimestamp(stat.st_mtime)
        is_dir = S_ISDIR(stat.st_mode)
        icon = "📁" if is_dir else "📄"
        file_name = path.name
        if is_dir:
            file_name += "/"
        display = self.FILE_LINE_HTML.format(
            icon=icon,
            file_name=file_name,
            file_access=modified.isoformat(),
            file_size=stat.st_size,
        )
        return is_dir * -1, file_name, display
