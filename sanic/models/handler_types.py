from asyncio.events import AbstractEventLoop
from typing import Any, Callable, Coroutine, Optional, TypeVar, Union

import sanic

from sanic import request
from sanic.response import BaseHTTPResponse, HTTPResponse


Sanic = TypeVar("Sanic", bound="sanic.Sanic")
Request = TypeVar("Request", bound="request.Request")

MiddlewareResponse = Union[
    Optional[HTTPResponse], Coroutine[Any, Any, Optional[HTTPResponse]]
]
RequestMiddlewareType = Callable[[Request], MiddlewareResponse]
ResponseMiddlewareType = Callable[
    [Request, BaseHTTPResponse], MiddlewareResponse
]
ErrorMiddlewareType = Callable[
    [Request, BaseException], Optional[Coroutine[Any, Any, None]]
]
MiddlewareType = Union[RequestMiddlewareType, ResponseMiddlewareType]
ListenerType = Union[
    Callable[[Sanic], Optional[Coroutine[Any, Any, None]]],
    Callable[[Sanic, AbstractEventLoop], Optional[Coroutine[Any, Any, None]]],
]
RouteHandler = Callable[..., Coroutine[Any, Any, Optional[HTTPResponse]]]
SignalHandler = Callable[..., Coroutine[Any, Any, None]]
