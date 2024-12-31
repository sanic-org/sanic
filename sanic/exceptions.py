from asyncio import CancelledError
from collections.abc import Sequence
from os import PathLike
from typing import Any, Optional, Union

from sanic.helpers import STATUS_CODES
from sanic.models.protocol_types import Range


class RequestCancelled(CancelledError):
    quiet = True


class ServerKilled(Exception):
    """Exception Sanic server uses when killing a server process for something unexpected happening."""  # noqa: E501

    quiet = True


class SanicException(Exception):
    """Generic exception that will generate an HTTP response when raised in the context of a request lifecycle.

    Usually, it is best practice to use one of the more specific exceptions
    than this generic one. Even when trying to raise a 500, it is generally
    preferable to use `ServerError`.

    Args:
        message (Optional[Union[str, bytes]], optional): The message to be sent to the client. If `None`,
            then the appropriate HTTP response status message will be used instead. Defaults to `None`.
        status_code (Optional[int], optional): The HTTP response code to send, if applicable. If `None`,
            then it will be 500. Defaults to `None`.
        quiet (Optional[bool], optional): When `True`, the error traceback will be suppressed from the logs.
            Defaults to `None`.
        context (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will be
            sent to the client upon exception. Defaults to `None`.
        extra (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will NOT be
            sent to the client when in PRODUCTION mode. Defaults to `None`.
        headers (Optional[Dict[str, Any]], optional): Additional headers that should be sent with the HTTP
            response. Defaults to `None`.

    Examples:
        ```python
        raise SanicException(
            "Something went wrong",
            status_code=999,
            context={
                "info": "Some additional details to send to the client",
            },
            headers={
                "X-Foo": "bar"
            }
        )
        ```
    """  # noqa: E501

    status_code: int = 500
    quiet: Optional[bool] = False
    headers: dict[str, str] = {}
    message: str = ""

    def __init__(
        self,
        message: Optional[Union[str, bytes]] = None,
        status_code: Optional[int] = None,
        *,
        quiet: Optional[bool] = None,
        context: Optional[dict[str, Any]] = None,
        extra: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        self.context = context
        self.extra = extra
        status_code = status_code or getattr(
            self.__class__, "status_code", None
        )
        quiet = (
            quiet
            if quiet is not None
            else getattr(self.__class__, "quiet", None)
        )
        headers = headers or getattr(self.__class__, "headers", {})
        if message is None:
            message = self.message
            if not message and status_code:
                msg = STATUS_CODES.get(status_code, b"")
                message = msg.decode()
        elif isinstance(message, bytes):
            message = message.decode()

        super().__init__(message)

        self.status_code = status_code or self.status_code
        self.quiet = quiet
        self.headers = headers
        try:
            self.message = message
        except AttributeError:
            ...


class HTTPException(SanicException):
    """A base class for other exceptions and should not be called directly."""

    def __init__(
        self,
        message: Optional[Union[str, bytes]] = None,
        *,
        quiet: Optional[bool] = None,
        context: Optional[dict[str, Any]] = None,
        extra: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message,
            quiet=quiet,
            context=context,
            extra=extra,
            headers=headers,
        )


class NotFound(HTTPException):
    """A base class for other exceptions and should not be called directly.

    Args:
        message (Optional[Union[str, bytes]], optional): The message to be sent to the client. If `None`,
            then the appropriate HTTP response status message will be used instead. Defaults to `None`.
        quiet (Optional[bool], optional): When `True`, the error traceback will be suppressed from the logs.
            Defaults to `None`.
        context (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will be
            sent to the client upon exception. Defaults to `None`.
        extra (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will NOT be
            sent to the client when in PRODUCTION mode. Defaults to `None`.
        headers (Optional[Dict[str, Any]], optional): Additional headers that should be sent with the HTTP
            response. Defaults to `None`.
    """  # noqa: E501

    status_code = 404
    quiet = True


class BadRequest(HTTPException):
    """400 Bad Request

    Args:
        message (Optional[Union[str, bytes]], optional): The message to be sent to the client. If `None`
            then the HTTP status 'Bad Request' will be sent. Defaults to `None`.
        quiet (Optional[bool], optional): When `True`, the error traceback will be suppressed
            from the logs. Defaults to `None`.
        context (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will be
            sent to the client upon exception. Defaults to `None`.
        extra (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will NOT be
            sent to the client when in PRODUCTION mode. Defaults to `None`.
        headers (Optional[Dict[str, Any]], optional): Additional headers that should be sent with the HTTP
            response. Defaults to `None`.
    """  # noqa: E501

    status_code = 400
    quiet = True


InvalidUsage = BadRequest
BadURL = BadRequest


class MethodNotAllowed(HTTPException):
    """405 Method Not Allowed

    Args:
        message (Optional[Union[str, bytes]], optional): The message to be sent to the client. If `None`
            then the HTTP status 'Method Not Allowed' will be sent. Defaults to `None`.
        method (Optional[str], optional): The HTTP method that was used. Defaults to an empty string.
        allowed_methods (Optional[Sequence[str]], optional): The HTTP methods that can be used instead of the
            one that was attempted.
        quiet (Optional[bool], optional): When `True`, the error traceback will be suppressed
            from the logs. Defaults to `None`.
        context (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will be
            sent to the client upon exception. Defaults to `None`.
        extra (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will NOT be
            sent to the client when in PRODUCTION mode. Defaults to `None`.
        headers (Optional[Dict[str, Any]], optional): Additional headers that should be sent with the HTTP
            response. Defaults to `None`.
    """  # noqa: E501

    status_code = 405
    quiet = True

    def __init__(
        self,
        message: Optional[Union[str, bytes]] = None,
        method: str = "",
        allowed_methods: Optional[Sequence[str]] = None,
        *,
        quiet: Optional[bool] = None,
        context: Optional[dict[str, Any]] = None,
        extra: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message,
            quiet=quiet,
            context=context,
            extra=extra,
            headers=headers,
        )
        if allowed_methods:
            self.headers = {
                **self.headers,
                "Allow": ", ".join(allowed_methods),
            }
        self.method = method
        self.allowed_methods = allowed_methods


MethodNotSupported = MethodNotAllowed


class ServerError(HTTPException):
    """500 Internal Server Error

    A general server-side error has occurred. If no other HTTP exception is
    appropriate, then this should be used

    Args:
        message (Optional[Union[str, bytes]], optional): The message to be sent to the client. If `None`
            then the HTTP status 'Bad Request' will be sent. Defaults to `None`.
        quiet (Optional[bool], optional): When `True`, the error traceback will be suppressed
            from the logs. Defaults to `None`.
        context (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will be
            sent to the client upon exception. Defaults to `None`.
        extra (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will NOT be
            sent to the client when in PRODUCTION mode. Defaults to `None`.
        headers (Optional[Dict[str, Any]], optional): Additional headers that should be sent with the HTTP
            response. Defaults to `None`.
    """  # noqa: E501

    status_code = 500


InternalServerError = ServerError


class ServiceUnavailable(HTTPException):
    """503 Service Unavailable

    The server is currently unavailable (because it is overloaded or
    down for maintenance). Generally, this is a temporary state.

    Args:
        message (Optional[Union[str, bytes]], optional): The message to be sent to the client. If `None`
            then the HTTP status 'Bad Request' will be sent. Defaults to `None`.
        quiet (Optional[bool], optional): When `True`, the error traceback will be suppressed
            from the logs. Defaults to `None`.
        context (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will be
            sent to the client upon exception. Defaults to `None`.
        extra (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will NOT be
            sent to the client when in PRODUCTION mode. Defaults to `None`.
        headers (Optional[Dict[str, Any]], optional): Additional headers that should be sent with the HTTP
            response. Defaults to `None`.
    """  # noqa: E501

    status_code = 503
    quiet = True


class URLBuildError(HTTPException):
    """500 Internal Server Error

    An exception used by Sanic internals when unable to build a URL.

    Args:
        message (Optional[Union[str, bytes]], optional): The message to be sent to the client. If `None`
            then the HTTP status 'Bad Request' will be sent. Defaults to `None`.
        quiet (Optional[bool], optional): When `True`, the error traceback will be suppressed
            from the logs. Defaults to `None`.
        context (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will be
            sent to the client upon exception. Defaults to `None`.
        extra (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will NOT be
            sent to the client when in PRODUCTION mode. Defaults to `None`.
        headers (Optional[Dict[str, Any]], optional): Additional headers that should be sent with the HTTP
            response. Defaults to `None`.
    """  # noqa: E501

    status_code = 500


class FileNotFound(NotFound):
    """404 Not Found

    A specific form of :class:`.NotFound` that is specifically when looking
    for a file on the file system at a known path.

    Args:
        message (Optional[Union[str, bytes]], optional): The message to be sent to the client. If `None`
            then the HTTP status 'Not Found' will be sent. Defaults to `None`.
        path (Optional[PathLike], optional): The path, if any, to the file that could not
            be found. Defaults to `None`.
        relative_url (Optional[str], optional): A relative URL of the file. Defaults to `None`.
        quiet (Optional[bool], optional): When `True`, the error traceback will be suppressed
            from the logs. Defaults to `None`.
        context (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will be
            sent to the client upon exception. Defaults to `None`.
        extra (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will NOT be
            sent to the client when in PRODUCTION mode. Defaults to `None`.
        headers (Optional[Dict[str, Any]], optional): Additional headers that should be sent with the HTTP
            response. Defaults to `None`.
    """  # noqa: E501

    def __init__(
        self,
        message: Optional[Union[str, bytes]] = None,
        path: Optional[PathLike] = None,
        relative_url: Optional[str] = None,
        *,
        quiet: Optional[bool] = None,
        context: Optional[dict[str, Any]] = None,
        extra: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message,
            quiet=quiet,
            context=context,
            extra=extra,
            headers=headers,
        )
        self.path = path
        self.relative_url = relative_url


class RequestTimeout(HTTPException):
    """408 Request Timeout

    The Web server (running the Web site) thinks that there has been too
    long an interval of time between 1) the establishment of an IP
    connection (socket) between the client and the server and
    2) the receipt of any data on that socket, so the server has dropped
    the connection. The socket connection has actually been lost - the Web
    server has 'timed out' on that particular socket connection.

    This is an internal exception thrown by Sanic and should not be used
    directly.

    Args:
        message (Optional[Union[str, bytes]], optional): The message to be sent to the client. If `None`
            then the HTTP status 'Bad Request' will be sent. Defaults to `None`.
        quiet (Optional[bool], optional): When `True`, the error traceback will be suppressed
            from the logs. Defaults to `None`.
        context (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will be
            sent to the client upon exception. Defaults to `None`.
        extra (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will NOT be
            sent to the client when in PRODUCTION mode. Defaults to `None`.
        headers (Optional[Dict[str, Any]], optional): Additional headers that should be sent with the HTTP
            response. Defaults to `None`.
    """  # noqa: E501

    status_code = 408
    quiet = True


class PayloadTooLarge(HTTPException):
    """413 Payload Too Large

    This is an internal exception thrown by Sanic and should not be used
    directly.

    Args:
        message (Optional[Union[str, bytes]], optional): The message to be sent to the client. If `None`
            then the HTTP status 'Bad Request' will be sent. Defaults to `None`.
        quiet (Optional[bool], optional): When `True`, the error traceback will be suppressed
            from the logs. Defaults to `None`.
        context (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will be
            sent to the client upon exception. Defaults to `None`.
        extra (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will NOT be
            sent to the client when in PRODUCTION mode. Defaults to `None`.
        headers (Optional[Dict[str, Any]], optional): Additional headers that should be sent with the HTTP
            response. Defaults to `None`.
    """  # noqa: E501

    status_code = 413
    quiet = True


class HeaderNotFound(BadRequest):
    """400 Bad Request

    Args:
        message (Optional[Union[str, bytes]], optional): The message to be sent to the client. If `None`
            then the HTTP status 'Bad Request' will be sent. Defaults to `None`.
        quiet (Optional[bool], optional): When `True`, the error traceback will be suppressed
            from the logs. Defaults to `None`.
        context (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will be
            sent to the client upon exception. Defaults to `None`.
        extra (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will NOT be
            sent to the client when in PRODUCTION mode. Defaults to `None`.
        headers (Optional[Dict[str, Any]], optional): Additional headers that should be sent with the HTTP
            response. Defaults to `None`.
    """  # noqa: E501


class InvalidHeader(BadRequest):
    """400 Bad Request

    Args:
        message (Optional[Union[str, bytes]], optional): The message to be sent to the client. If `None`
            then the HTTP status 'Bad Request' will be sent. Defaults to `None`.
        quiet (Optional[bool], optional): When `True`, the error traceback will be suppressed
            from the logs. Defaults to `None`.
        context (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will be
            sent to the client upon exception. Defaults to `None`.
        extra (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will NOT be
            sent to the client when in PRODUCTION mode. Defaults to `None`.
        headers (Optional[Dict[str, Any]], optional): Additional headers that should be sent with the HTTP
            response. Defaults to `None`.
    """  # noqa: E501


class RangeNotSatisfiable(HTTPException):
    """416 Range Not Satisfiable

    Args:
        message (Optional[Union[str, bytes]], optional): The message to be sent to the client. If `None`
            then the HTTP status 'Range Not Satisfiable' will be sent. Defaults to `None`.
        content_range (Optional[ContentRange], optional): An object meeting the :class:`.ContentRange` protocol
            that has a `total` property. Defaults to `None`.
        quiet (Optional[bool], optional): When `True`, the error traceback will be suppressed
            from the logs. Defaults to `None`.
        context (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will be
            sent to the client upon exception. Defaults to `None`.
        extra (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will NOT be
            sent to the client when in PRODUCTION mode. Defaults to `None`.
        headers (Optional[Dict[str, Any]], optional): Additional headers that should be sent with the HTTP
            response. Defaults to `None`.
    """  # noqa: E501

    status_code = 416
    quiet = True

    def __init__(
        self,
        message: Optional[Union[str, bytes]] = None,
        content_range: Optional[Range] = None,
        *,
        quiet: Optional[bool] = None,
        context: Optional[dict[str, Any]] = None,
        extra: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message,
            quiet=quiet,
            context=context,
            extra=extra,
            headers=headers,
        )
        if content_range is not None:
            self.headers = {
                **self.headers,
                "Content-Range": f"bytes */{content_range.total}",
            }


ContentRangeError = RangeNotSatisfiable


class ExpectationFailed(HTTPException):
    """417 Expectation Failed

    Args:
        message (Optional[Union[str, bytes]], optional): The message to be sent to the client. If `None`
            then the HTTP status 'Bad Request' will be sent. Defaults to `None`.
        quiet (Optional[bool], optional): When `True`, the error traceback will be suppressed
            from the logs. Defaults to `None`.
        context (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will be
            sent to the client upon exception. Defaults to `None`.
        extra (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will NOT be
            sent to the client when in PRODUCTION mode. Defaults to `None`.
        headers (Optional[Dict[str, Any]], optional): Additional headers that should be sent with the HTTP
            response. Defaults to `None`.
    """  # noqa: E501

    status_code = 417
    quiet = True


HeaderExpectationFailed = ExpectationFailed


class Forbidden(HTTPException):
    """403 Forbidden

    Args:
        message (Optional[Union[str, bytes]], optional): The message to be sent to the client. If `None`
            then the HTTP status 'Bad Request' will be sent. Defaults to `None`.
        quiet (Optional[bool], optional): When `True`, the error traceback will be suppressed
            from the logs. Defaults to `None`.
        context (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will be
            sent to the client upon exception. Defaults to `None`.
        extra (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will NOT be
            sent to the client when in PRODUCTION mode. Defaults to `None`.
        headers (Optional[Dict[str, Any]], optional): Additional headers that should be sent with the HTTP
            response. Defaults to `None`.
    """  # noqa: E501

    status_code = 403
    quiet = True


class InvalidRangeType(RangeNotSatisfiable):
    """416 Range Not Satisfiable

    Args:
        message (Optional[Union[str, bytes]], optional): The message to be sent to the client. If `None`
            then the HTTP status 'Bad Request' will be sent. Defaults to `None`.
        quiet (Optional[bool], optional): When `True`, the error traceback will be suppressed
            from the logs. Defaults to `None`.
        context (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will be
            sent to the client upon exception. Defaults to `None`.
        extra (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will NOT be
            sent to the client when in PRODUCTION mode. Defaults to `None`.
        headers (Optional[Dict[str, Any]], optional): Additional headers that should be sent with the HTTP
            response. Defaults to `None`.
    """  # noqa: E501

    status_code = 416
    quiet = True


class PyFileError(SanicException):
    def __init__(
        self,
        file,
        status_code: Optional[int] = None,
        *,
        quiet: Optional[bool] = None,
        context: Optional[dict[str, Any]] = None,
        extra: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            "could not execute config file %s" % file,
            status_code=status_code,
            quiet=quiet,
            context=context,
            extra=extra,
            headers=headers,
        )


class Unauthorized(HTTPException):
    """
    **Status**: 401 Unauthorized

    When present, additional keyword arguments may be used to complete
    the WWW-Authentication header.

    Args:
        message (Optional[Union[str, bytes]], optional): The message to be sent to the client. If `None`
            then the HTTP status 'Bad Request' will be sent. Defaults to `None`.
        scheme (Optional[str], optional): Name of the authentication scheme to be used. Defaults to `None`.
        quiet (Optional[bool], optional): When `True`, the error traceback will be suppressed
            from the logs. Defaults to `None`.
        context (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will be
            sent to the client upon exception. Defaults to `None`.
        extra (Optional[Dict[str, Any]], optional): Additional mapping of key/value data that will NOT be
            sent to the client when in PRODUCTION mode. Defaults to `None`.
        headers (Optional[Dict[str, Any]], optional): Additional headers that should be sent with the HTTP
            response. Defaults to `None`.
        **challenges (Dict[str, Any]): Additional keyword arguments that will be used to complete the
            WWW-Authentication header. Defaults to `None`.

    Examples:
        With a Basic auth-scheme, realm MUST be present:
        ```python
        raise Unauthorized(
            "Auth required.",
            scheme="Basic",
            realm="Restricted Area"
        )
        ```

        With a Digest auth-scheme, things are a bit more complicated:
        ```python
        raise Unauthorized(
            "Auth required.",
            scheme="Digest",
            realm="Restricted Area",
            qop="auth, auth-int",
            algorithm="MD5",
            nonce="abcdef",
            opaque="zyxwvu"
        )
        ```

        With a Bearer auth-scheme, realm is optional so you can write:
        ```python
        raise Unauthorized("Auth required.", scheme="Bearer")
        ```

        or, if you want to specify the realm:
        ```python
        raise Unauthorized(
            "Auth required.",
            scheme="Bearer",
            realm="Restricted Area"
        )
        ```
    """  # noqa: E501

    status_code = 401
    quiet = True

    def __init__(
        self,
        message: Optional[Union[str, bytes]] = None,
        scheme: Optional[str] = None,
        *,
        quiet: Optional[bool] = None,
        context: Optional[dict[str, Any]] = None,
        extra: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, Any]] = None,
        **challenges,
    ):
        super().__init__(
            message,
            quiet=quiet,
            context=context,
            extra=extra,
            headers=headers,
        )

        # if auth-scheme is specified, set "WWW-Authenticate" header
        if scheme is not None:
            values = [f'{k!s}="{v!s}"' for k, v in challenges.items()]
            challenge = ", ".join(values)

            self.headers = {
                **self.headers,
                "WWW-Authenticate": f"{scheme} {challenge}".rstrip(),
            }


class LoadFileException(SanicException):
    """Exception raised when a file cannot be loaded."""


class InvalidSignal(SanicException):
    """Exception raised when an invalid signal is sent."""


class WebsocketClosed(SanicException):
    """Exception raised when a websocket is closed."""

    quiet = True
    message = "Client has closed the websocket connection"
