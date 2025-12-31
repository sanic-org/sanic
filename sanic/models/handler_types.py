from asyncio.events import AbstractEventLoop
from collections.abc import Coroutine
from typing import Any, Callable, TypeVar

import sanic

from sanic import request
from sanic.response import BaseHTTPResponse, HTTPResponse


Sanic = TypeVar("Sanic", bound="sanic.Sanic")
Request = TypeVar("Request", bound="request.Request")

MiddlewareResponse = (
    HTTPResponse | None | Coroutine[Any, Any, HTTPResponse | None]
)
RequestMiddlewareType = Callable[[Request], MiddlewareResponse]
ResponseMiddlewareType = Callable[
    [Request, BaseHTTPResponse], MiddlewareResponse
]
ErrorMiddlewareType = Callable[
    [Request, BaseException], Coroutine[Any, Any, None] | None
]
MiddlewareType = RequestMiddlewareType | ResponseMiddlewareType
ListenerType = (
    Callable[[Sanic], Coroutine[Any, Any, None] | None]
    | Callable[[Sanic, AbstractEventLoop], Coroutine[Any, Any, None] | None]
)
RouteHandler = Callable[..., Coroutine[Any, Any, HTTPResponse | None]]
SignalHandler = Callable[..., Coroutine[Any, Any, None]]
