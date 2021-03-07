from pathlib import PurePath
from typing import NamedTuple, List, Union, Iterable

from sanic.models.handler_types import (
    ListenerType,
    MiddlewareType,
    ErrorMiddlewareType,
)


class FutureRoute(NamedTuple):
    handler: str
    uri: str
    methods: Union[None, Iterable[str]]
    host: str
    strict_slashes: bool
    stream: bool
    version: Union[None, int]
    name: str
    ignore_body: bool
    websocket: bool
    subprotocols: Union[None, List[str]]
    unquote: bool
    static: bool


class FutureListener(NamedTuple):
    listener: ListenerType
    event: str


class FutureMiddleware(NamedTuple):
    middleware: MiddlewareType
    attach_to: str


class FutureException(NamedTuple):
    handler: ErrorMiddlewareType
    exceptions: List[BaseException]


class FutureStatic(NamedTuple):
    uri: str
    file_or_directory: Union[str, bytes, PurePath]
    pattern: str
    use_modified_since: bool
    use_content_range: bool
    stream_large_files: bool
    name: str
    host: Union[None, str]
    strict_slashes: Union[None, bool]
    content_type: Union[None, bool]
