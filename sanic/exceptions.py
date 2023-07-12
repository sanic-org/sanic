from asyncio import CancelledError, Protocol
from os import PathLike
from typing import Any, Dict, Optional, Sequence, Union

from sanic.helpers import STATUS_CODES


class RequestCancelled(CancelledError):
    quiet = True


class ServerKilled(Exception):
    """
    Exception Sanic server uses when killing a server process for something
    unexpected happening.
    """


class SanicException(Exception):
    """
    Generic exception that will generate an HTTP response when raised
    in the context of a request lifecycle.

    Usually it is best practice to use one of the more specific exceptions
    than this generic. Even when trying to raise a 500, it is generally
    preferrable to use :class:`.ServerError`

    .. code-block:: python

        raise SanicException(
            "Something went wrong",
            status_code=999,
            context={
                "info": "Some additional details",
            },
            headers={
                "X-Foo": "bar"
            }
        )

    :param message: The message to be sent to the client. If ``None``
        then the appropriate HTTP response status message will be used
        instead, defaults to None
    :type message: Optional[Union[str, bytes]], optional
    :param status_code: The HTTP response code to send, if applicable. If
        ``None``, then it will be 500, defaults to None
    :type status_code: Optional[int], optional
    :param quiet: When ``True``, the error traceback will be suppressed
        from the logs, defaults to None
    :type quiet: Optional[bool], optional
    :param context: Additional mapping of key/value data that will be
        sent to the client upon exception, defaults to None
    :type context: Optional[Dict[str, Any]], optional
    :param extra: Additional mapping of key/value data that will NOT be
        sent to the client when in PRODUCTION mode, defaults to None
    :type extra: Optional[Dict[str, Any]], optional
    :param headers: Additional headers that should be sent with the HTTP
        response, defaults to None
    :type headers: Optional[Dict[str, Any]], optional
    """

    status_code: int = 500
    quiet: Optional[bool] = False
    headers: Dict[str, str] = {}
    message: str = ""

    def __init__(
        self,
        message: Optional[Union[str, bytes]] = None,
        status_code: Optional[int] = None,
        *,
        quiet: Optional[bool] = None,
        context: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.context = context
        self.extra = extra
        status_code = status_code or getattr(
            self.__class__, "status_code", None
        )
        quiet = quiet or getattr(self.__class__, "quiet", None)
        headers = headers or getattr(self.__class__, "headers", {})
        if message is None:
            if self.message:
                message = self.message
            elif status_code:
                msg: bytes = STATUS_CODES.get(status_code, b"")
                message = msg.decode("utf8")

        super().__init__(message)

        self.status_code = status_code or self.status_code
        self.quiet = quiet
        self.headers = headers


class HTTPException(SanicException):
    """
    A base class for other exceptions and should not be called directly.
    """

    def __init__(
        self,
        message: Optional[Union[str, bytes]] = None,
        *,
        quiet: Optional[bool] = None,
        context: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message,
            quiet=quiet,
            context=context,
            extra=extra,
            headers=headers,
        )


class NotFound(HTTPException):
    """
    **Status**: 404 Not Found

    :param message: The message to be sent to the client. If ``None``
        then the HTTP status 'Not Found' will be sent, defaults to None
    :type message: Optional[Union[str, bytes]], optional
    :param quiet: When ``True``, the error traceback will be suppressed
        from the logs, defaults to None
    :type quiet: Optional[bool], optional
    :param context: Additional mapping of key/value data that will be
        sent to the client upon exception, defaults to None
    :type context: Optional[Dict[str, Any]], optional
    :param extra: Additional mapping of key/value data that will NOT be
        sent to the client when in PRODUCTION mode, defaults to None
    :type extra: Optional[Dict[str, Any]], optional
    :param headers: Additional headers that should be sent with the HTTP
        response, defaults to None
    :type headers: Optional[Dict[str, Any]], optional
    """

    status_code = 404
    quiet = True


class BadRequest(HTTPException):
    """
    **Status**: 400 Bad Request

    :param message: The message to be sent to the client. If ``None``
        then the HTTP status 'Bad Request' will be sent, defaults to None
    :type message: Optional[Union[str, bytes]], optional
    :param quiet: When ``True``, the error traceback will be suppressed
        from the logs, defaults to None
    :type quiet: Optional[bool], optional
    :param context: Additional mapping of key/value data that will be
        sent to the client upon exception, defaults to None
    :type context: Optional[Dict[str, Any]], optional
    :param extra: Additional mapping of key/value data that will NOT be
        sent to the client when in PRODUCTION mode, defaults to None
    :type extra: Optional[Dict[str, Any]], optional
    :param headers: Additional headers that should be sent with the HTTP
        response, defaults to None
    :type headers: Optional[Dict[str, Any]], optional
    """

    status_code = 400
    quiet = True


InvalidUsage = BadRequest
BadURL = BadRequest


class MethodNotAllowed(HTTPException):
    """
    **Status**: 405 Method Not Allowed

    :param message: The message to be sent to the client. If ``None``
        then the HTTP status 'Method Not Allowed' will be sent,
        defaults to None
    :type message: Optional[Union[str, bytes]], optional
    :param method: The HTTP method that was used, defaults to  an empty string
    :type method: Optional[str], optional
    :param allowed_methods: The HTTP methods that can be used instead of the
        one that was attempted
    :type allowed_methods: Optional[Sequence[str]], optional
    :param quiet: When ``True``, the error traceback will be suppressed
        from the logs, defaults to None
    :type quiet: Optional[bool], optional
    :param context: Additional mapping of key/value data that will be
        sent to the client upon exception, defaults to None
    :type context: Optional[Dict[str, Any]], optional
    :param extra: Additional mapping of key/value data that will NOT be
        sent to the client when in PRODUCTION mode, defaults to None
    :type extra: Optional[Dict[str, Any]], optional
    :param headers: Additional headers that should be sent with the HTTP
        response, defaults to None
    :type headers: Optional[Dict[str, Any]], optional
    """

    status_code = 405
    quiet = True

    def __init__(
        self,
        message: Optional[Union[str, bytes]] = None,
        method: str = "",
        allowed_methods: Optional[Sequence[str]] = None,
        *,
        quiet: Optional[bool] = None,
        context: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
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
    """
    **Status**: 500 Internal Server Error

    A general server-side error has occurred. If no other HTTP exception is
    appropriate, then this should be used

    :param message: The message to be sent to the client. If ``None``
        then the HTTP status 'Internal Server Error' will be sent,
         defaults to None
    :type message: Optional[Union[str, bytes]], optional
    :param quiet: When ``True``, the error traceback will be suppressed
        from the logs, defaults to None
    :type quiet: Optional[bool], optional
    :param context: Additional mapping of key/value data that will be
        sent to the client upon exception, defaults to None
    :type context: Optional[Dict[str, Any]], optional
    :param extra: Additional mapping of key/value data that will NOT be
        sent to the client when in PRODUCTION mode, defaults to None
    :type extra: Optional[Dict[str, Any]], optional
    :param headers: Additional headers that should be sent with the HTTP
        response, defaults to None
    :type headers: Optional[Dict[str, Any]], optional
    """

    status_code = 500


InternalServerError = ServerError


class ServiceUnavailable(HTTPException):
    """
    **Status**: 503 Service Unavailable

    The server is currently unavailable (because it is overloaded or
    down for maintenance). Generally, this is a temporary state.

    :param message: The message to be sent to the client. If ``None``
        then the HTTP status 'Bad Request' will be sent, defaults to None
    :type message: Optional[Union[str, bytes]], optional
    :param quiet: When ``True``, the error traceback will be suppressed
        from the logs, defaults to None
    :type quiet: Optional[bool], optional
    :param context: Additional mapping of key/value data that will be
        sent to the client upon exception, defaults to None
    :type context: Optional[Dict[str, Any]], optional
    :param extra: Additional mapping of key/value data that will NOT be
        sent to the client when in PRODUCTION mode, defaults to None
    :type extra: Optional[Dict[str, Any]], optional
    :param headers: Additional headers that should be sent with the HTTP
        response, defaults to None
    :type headers: Optional[Dict[str, Any]], optional
    """

    status_code = 503
    quiet = True


class URLBuildError(HTTPException):
    """
    **Status**: 500 Internal Server Error

    An exception used by Sanic internals when unable to build a URL.
    """

    status_code = 500


class FileNotFound(NotFound):
    """
    **Status**: 404 Not Found

    A specific form of :class:`.NotFound` that is specifically when looking
    for a file on the file system at a known path.

    :param message: The message to be sent to the client. If ``None``
        then the HTTP status 'Not Found' will be sent, defaults to None
    :type message: Optional[Union[str, bytes]], optional
    :param path: The path, if any, to the file that could not
        be found, defaults to None
    :type path: Optional[PathLike], optional
    :param relative_url: A relative URL of the file, defaults to None
    :type relative_url: Optional[str], optional
    :param quiet: When ``True``, the error traceback will be suppressed
        from the logs, defaults to None
    :type quiet: Optional[bool], optional
    :param context: Additional mapping of key/value data that will be
        sent to the client upon exception, defaults to None
    :type context: Optional[Dict[str, Any]], optional
    :param extra: Additional mapping of key/value data that will NOT be
        sent to the client when in PRODUCTION mode, defaults to None
    :type extra: Optional[Dict[str, Any]], optional
    :param headers: Additional headers that should be sent with the HTTP
        response, defaults to None
    :type headers: Optional[Dict[str, Any]], optional
    """

    def __init__(
        self,
        message: Optional[Union[str, bytes]] = None,
        path: Optional[PathLike] = None,
        relative_url: Optional[str] = None,
        *,
        quiet: Optional[bool] = None,
        context: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
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
    """
    The Web server (running the Web site) thinks that there has been too
    long an interval of time between 1) the establishment of an IP
    connection (socket) between the client and the server and
    2) the receipt of any data on that socket, so the server has dropped
    the connection. The socket connection has actually been lost - the Web
    server has 'timed out' on that particular socket connection.

    This is an internal exception thrown by Sanic and should not be used
    directly.
    """

    status_code = 408
    quiet = True


class PayloadTooLarge(HTTPException):
    """
    **Status**: 413 Payload Too Large

    This is an internal exception thrown by Sanic and should not be used
    directly.
    """

    status_code = 413
    quiet = True


class HeaderNotFound(BadRequest):
    """
    **Status**: 400 Bad Request

    :param message: The message to be sent to the client. If ``None``
        then the HTTP status 'Bad Request' will be sent, defaults to None
    :type message: Optional[Union[str, bytes]], optional
    :param quiet: When ``True``, the error traceback will be suppressed
        from the logs, defaults to None
    :type quiet: Optional[bool], optional
    :param context: Additional mapping of key/value data that will be
        sent to the client upon exception, defaults to None
    :type context: Optional[Dict[str, Any]], optional
    :param extra: Additional mapping of key/value data that will NOT be
        sent to the client when in PRODUCTION mode, defaults to None
    :type extra: Optional[Dict[str, Any]], optional
    :param headers: Additional headers that should be sent with the HTTP
        response, defaults to None
    :type headers: Optional[Dict[str, Any]], optional
    """


class InvalidHeader(BadRequest):
    """
    **Status**: 400 Bad Request

    :param message: The message to be sent to the client. If ``None``
        then the HTTP status 'Bad Request' will be sent, defaults to None
    :type message: Optional[Union[str, bytes]], optional
    :param quiet: When ``True``, the error traceback will be suppressed
        from the logs, defaults to None
    :type quiet: Optional[bool], optional
    :param context: Additional mapping of key/value data that will be
        sent to the client upon exception, defaults to None
    :type context: Optional[Dict[str, Any]], optional
    :param extra: Additional mapping of key/value data that will NOT be
        sent to the client when in PRODUCTION mode, defaults to None
    :type extra: Optional[Dict[str, Any]], optional
    :param headers: Additional headers that should be sent with the HTTP
        response, defaults to None
    :type headers: Optional[Dict[str, Any]], optional
    """


class ContentRange(Protocol):
    total: int


class RangeNotSatisfiable(HTTPException):
    """
    **Status**: 416 Range Not Satisfiable

    :param message: The message to be sent to the client. If ``None``
        then the HTTP status 'Range Not Satisfiable' will be sent,
        defaults to None
    :type message: Optional[Union[str, bytes]], optional
    :param content_range: An object meeting the :class:`.ContentRange` protocol
        that has a ``total`` property, defaults to None
    :type content_range: Optional[ContentRange], optional
    :param quiet: When ``True``, the error traceback will be suppressed
        from the logs, defaults to None
    :type quiet: Optional[bool], optional
    :param context: Additional mapping of key/value data that will be
        sent to the client upon exception, defaults to None
    :type context: Optional[Dict[str, Any]], optional
    :param extra: Additional mapping of key/value data that will NOT be
        sent to the client when in PRODUCTION mode, defaults to None
    :type extra: Optional[Dict[str, Any]], optional
    :param headers: Additional headers that should be sent with the HTTP
        response, defaults to None
    :type headers: Optional[Dict[str, Any]], optional
    """

    status_code = 416
    quiet = True

    def __init__(
        self,
        message: Optional[Union[str, bytes]] = None,
        content_range: Optional[ContentRange] = None,
        *,
        quiet: Optional[bool] = None,
        context: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
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
    """
    **Status**: 417 Expectation Failed

    :param message: The message to be sent to the client. If ``None``
        then the HTTP status 'Expectation Failed' will be sent,
        defaults to None
    :type message: Optional[Union[str, bytes]], optional
    :param quiet: When ``True``, the error traceback will be suppressed
        from the logs, defaults to None
    :type quiet: Optional[bool], optional
    :param context: Additional mapping of key/value data that will be
        sent to the client upon exception, defaults to None
    :type context: Optional[Dict[str, Any]], optional
    :param extra: Additional mapping of key/value data that will NOT be
        sent to the client when in PRODUCTION mode, defaults to None
    :type extra: Optional[Dict[str, Any]], optional
    :param headers: Additional headers that should be sent with the HTTP
        response, defaults to None
    :type headers: Optional[Dict[str, Any]], optional
    """

    status_code = 417
    quiet = True


HeaderExpectationFailed = ExpectationFailed


class Forbidden(HTTPException):
    """
    **Status**: 403 Forbidden

    :param message: The message to be sent to the client. If ``None``
        then the HTTP status 'Forbidden' will be sent, defaults to None
    :type message: Optional[Union[str, bytes]], optional
    :param quiet: When ``True``, the error traceback will be suppressed
        from the logs, defaults to None
    :type quiet: Optional[bool], optional
    :param context: Additional mapping of key/value data that will be
        sent to the client upon exception, defaults to None
    :type context: Optional[Dict[str, Any]], optional
    :param extra: Additional mapping of key/value data that will NOT be
        sent to the client when in PRODUCTION mode, defaults to None
    :type extra: Optional[Dict[str, Any]], optional
    :param headers: Additional headers that should be sent with the HTTP
        response, defaults to None
    :type headers: Optional[Dict[str, Any]], optional
    """

    status_code = 403
    quiet = True


class InvalidRangeType(RangeNotSatisfiable):
    """
    **Status**: 416 Range Not Satisfiable
    """

    status_code = 416
    quiet = True


class PyFileError(SanicException):
    def __init__(
        self,
        file,
        status_code: Optional[int] = None,
        *,
        quiet: Optional[bool] = None,
        context: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
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

    Examples::

        # With a Basic auth-scheme, realm MUST be present:
        raise Unauthorized("Auth required.",
                           scheme="Basic",
                           realm="Restricted Area")

        # With a Digest auth-scheme, things are a bit more complicated:
        raise Unauthorized("Auth required.",
                           scheme="Digest",
                           realm="Restricted Area",
                           qop="auth, auth-int",
                           algorithm="MD5",
                           nonce="abcdef",
                           opaque="zyxwvu")

        # With a Bearer auth-scheme, realm is optional so you can write:
        raise Unauthorized("Auth required.", scheme="Bearer")

        # or, if you want to specify the realm:
        raise Unauthorized("Auth required.",
                           scheme="Bearer",
                           realm="Restricted Area")

    :param message: The message to be sent to the client. If ``None``
        then the HTTP status 'Bad Request' will be sent, defaults to None
    :type message: Optional[Union[str, bytes]], optional
    :param scheme: Name of the authentication scheme to be used.
    :type scheme: Optional[str], optional
    :param quiet: When ``True``, the error traceback will be suppressed
        from the logs, defaults to None
    :type quiet: Optional[bool], optional
    :param context: Additional mapping of key/value data that will be
        sent to the client upon exception, defaults to None
    :type context: Optional[Dict[str, Any]], optional
    :param extra: Additional mapping of key/value data that will NOT be
        sent to the client when in PRODUCTION mode, defaults to None
    :type extra: Optional[Dict[str, Any]], optional
    :param headers: Additional headers that should be sent with the HTTP
        response, defaults to None
    :type headers: Optional[Dict[str, Any]], optional
    """

    status_code = 401
    quiet = True

    def __init__(
        self,
        message: Optional[Union[str, bytes]] = None,
        scheme: Optional[str] = None,
        *,
        quiet: Optional[bool] = None,
        context: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
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
            values = [
                '{!s}="{!s}"'.format(k, v) for k, v in challenges.items()
            ]
            challenge = ", ".join(values)

            self.headers = {
                **self.headers,
                "WWW-Authenticate": f"{scheme} {challenge}".rstrip(),
            }


class LoadFileException(SanicException):
    pass


class InvalidSignal(SanicException):
    pass


class WebsocketClosed(SanicException):
    quiet = True
    message = "Client has closed the websocket connection"
