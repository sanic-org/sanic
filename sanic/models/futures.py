from pathlib import PurePath
from typing import Dict, Iterable, List, NamedTuple, Optional, Union

from sanic.models.handler_types import (
    ErrorMiddlewareType,
    ListenerType,
    MiddlewareType,
    SignalHandler,
)


class FutureRoute(NamedTuple):
    handler: str
    uri: str
    methods: Optional[Iterable[str]]
    host: str
    strict_slashes: bool
    stream: bool
    version: Optional[int]
    name: str
    ignore_body: bool
    websocket: bool
    subprotocols: Optional[List[str]]
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
    host: Optional[str]
    strict_slashes: Optional[bool]
    content_type: Optional[bool]


class FutureSignal(NamedTuple):
    handler: SignalHandler
    event: str
    condition: Optional[Dict[str, str]]
