from types import SimpleNamespace
from typing import TypeAlias

from sanic.__version__ import __version__
from sanic.app import Sanic
from sanic.blueprints import Blueprint
from sanic.config import Config
from sanic.constants import HTTPMethod
from sanic.exceptions import (
    BadRequest,
    ExpectationFailed,
    FileNotFound,
    Forbidden,
    HeaderNotFound,
    InternalServerError,
    InvalidHeader,
    MethodNotAllowed,
    NotFound,
    RangeNotSatisfiable,
    SanicException,
    ServerError,
    ServiceUnavailable,
    Unauthorized,
)
from sanic.request import Request
from sanic.response import (
    HTTPResponse,
    empty,
    file,
    html,
    json,
    raw,
    redirect,
    text,
)
from sanic.server.websockets.impl import WebsocketImplProtocol as Websocket

SimpleRequest: TypeAlias = Request[
    Sanic[Config, SimpleNamespace], SimpleNamespace
]

__all__ = (
    "__version__",
    # Common objects
    "Sanic",
    "Config",
    "Blueprint",
    "HTTPMethod",
    "HTTPResponse",
    "Request",
    "SimpleRequest",
    "Websocket",
    # Common exceptions
    "BadRequest",
    "ExpectationFailed",
    "FileNotFound",
    "Forbidden",
    "HeaderNotFound",
    "InternalServerError",
    "InvalidHeader",
    "MethodNotAllowed",
    "NotFound",
    "RangeNotSatisfiable",
    "SanicException",
    "ServerError",
    "ServiceUnavailable",
    "Unauthorized",
    # Common response methods
    "empty",
    "file",
    "html",
    "json",
    "raw",
    "redirect",
    "text",
)
