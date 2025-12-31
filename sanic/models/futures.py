from collections.abc import Iterable
from pathlib import Path
from typing import Callable, NamedTuple

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
    methods: Iterable[str] | None
    host: str | list[str]
    strict_slashes: bool
    stream: bool
    version: int | None
    name: str
    ignore_body: bool
    websocket: bool
    subprotocols: list[str] | None
    unquote: bool
    static: bool
    version_prefix: str
    error_format: str | None
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
    exceptions: list[BaseException]


class FutureStatic(NamedTuple):
    uri: str
    file_or_directory: Path
    pattern: str
    use_modified_since: bool
    use_content_range: bool
    stream_large_files: bool | int
    name: str
    host: str | None
    strict_slashes: bool | None
    content_type: str | None
    resource_type: str | None
    directory_handler: DirectoryHandler
    follow_external_symlink_files: bool
    follow_external_symlink_dirs: bool


class FutureSignal(NamedTuple):
    handler: SignalHandler
    event: str
    condition: dict[str, str] | None
    exclusive: bool
    priority: int


class FutureRegistry(set): ...


class FutureCommand(NamedTuple):
    name: str
    func: Callable
