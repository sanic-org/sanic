from pathlib import Path
from typing import Dict, Iterable, List, NamedTuple, Optional, Union

from sanic.handlers.directory import DirectoryHandler
from sanic.models.handler_types import (
    ErrorMiddlewareType,
    ListenerType,
    MiddlewareType,
    SignalHandler,
)
from sanic.types import HashableDict


class FutureRoute(NamedTuple):
    handler: str
    uri: str
    methods: Optional[Iterable[str]]
    host: Union[str, List[str]]
    strict_slashes: bool
    stream: bool
    version: Optional[int]
    name: str
    ignore_body: bool
    websocket: bool
    subprotocols: Optional[List[str]]
    unquote: bool
    static: bool
    version_prefix: str
    error_format: Optional[str]
    route_context: HashableDict


class FutureListener(NamedTuple):
    listener: ListenerType
    event: str
    priority: int


class FutureMiddleware(NamedTuple):
    middleware: MiddlewareType
    attach_to: str


class FutureException(NamedTuple):
    handler: ErrorMiddlewareType
    exceptions: List[BaseException]


class FutureStatic(NamedTuple):
    uri: str
    file_or_directory: Path
    pattern: str
    use_modified_since: bool
    use_content_range: bool
    stream_large_files: Union[bool, int]
    name: str
    host: Optional[str]
    strict_slashes: Optional[bool]
    content_type: Optional[str]
    resource_type: Optional[str]
    directory_handler: DirectoryHandler


class FutureSignal(NamedTuple):
    handler: SignalHandler
    event: str
    condition: Optional[Dict[str, str]]
    exclusive: bool
    priority: int


class FutureRegistry(set): ...
