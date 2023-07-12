from types import SimpleNamespace

from typing_extensions import TypeAlias

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


DefaultSanic: TypeAlias = "Sanic[Config, SimpleNamespace]"
"""
A type alias for a Sanic app with a default config and namespace.
"""

DefaultRequest: TypeAlias = Request[DefaultSanic, SimpleNamespace]
"""
A type alias for a request with a default Sanic app and namespace.
"""

__all__ = (
    "__version__",
    # Common objects
    "Sanic",
    "Config",
    "Blueprint",
    "HTTPMethod",
    "HTTPResponse",
    "Request",
    "Websocket",
    # Common types
    "DefaultSanic",
    "DefaultRequest",
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
