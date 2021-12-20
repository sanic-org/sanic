from typing import Any, Dict, Optional, Union

from sanic.helpers import STATUS_CODES


class SanicException(Exception):
    message: str = ""

    def __init__(
        self,
        message: Optional[Union[str, bytes]] = None,
        status_code: Optional[int] = None,
        quiet: Optional[bool] = None,
        context: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.context = context
        self.extra = extra
        if message is None:
            if self.message:
                message = self.message
            elif status_code is not None:
                msg: bytes = STATUS_CODES.get(status_code, b"")
                message = msg.decode("utf8")

        super().__init__(message)

        if status_code is not None:
            self.status_code = status_code

        # quiet=None/False/True with None meaning choose by status
        if quiet or quiet is None and status_code not in (None, 500):
            self.quiet = True


class NotFound(SanicException):
    """
    **Status**: 404 Not Found
    """

    status_code = 404
    quiet = True


class InvalidUsage(SanicException):
    """
    **Status**: 400 Bad Request
    """

    status_code = 400
    quiet = True


class MethodNotSupported(SanicException):
    """
    **Status**: 405 Method Not Allowed
    """

    status_code = 405
    quiet = True

    def __init__(self, message, method, allowed_methods):
        super().__init__(message)
        self.headers = {"Allow": ", ".join(allowed_methods)}


class ServerError(SanicException):
    """
    **Status**: 500 Internal Server Error
    """

    status_code = 500


class ServiceUnavailable(SanicException):
    """
    **Status**: 503 Service Unavailable

    The server is currently unavailable (because it is overloaded or
    down for maintenance). Generally, this is a temporary state.
    """

    status_code = 503
    quiet = True


class URLBuildError(ServerError):
    """
    **Status**: 500 Internal Server Error
    """

    status_code = 500


class FileNotFound(NotFound):
    """
    **Status**: 404 Not Found
    """

    def __init__(self, message, path, relative_url):
        super().__init__(message)
        self.path = path
        self.relative_url = relative_url


class RequestTimeout(SanicException):
    """The Web server (running the Web site) thinks that there has been too
    long an interval of time between 1) the establishment of an IP
    connection (socket) between the client and the server and
    2) the receipt of any data on that socket, so the server has dropped
    the connection. The socket connection has actually been lost - the Web
    server has 'timed out' on that particular socket connection.
    """

    status_code = 408
    quiet = True


class PayloadTooLarge(SanicException):
    """
    **Status**: 413 Payload Too Large
    """

    status_code = 413
    quiet = True


class HeaderNotFound(InvalidUsage):
    """
    **Status**: 400 Bad Request
    """


class InvalidHeader(InvalidUsage):
    """
    **Status**: 400 Bad Request
    """


class ContentRangeError(SanicException):
    """
    **Status**: 416 Range Not Satisfiable
    """

    status_code = 416
    quiet = True

    def __init__(self, message, content_range):
        super().__init__(message)
        self.headers = {"Content-Range": f"bytes */{content_range.total}"}


class HeaderExpectationFailed(SanicException):
    """
    **Status**: 417 Expectation Failed
    """

    status_code = 417
    quiet = True


class Forbidden(SanicException):
    """
    **Status**: 403 Forbidden
    """

    status_code = 403
    quiet = True


class InvalidRangeType(ContentRangeError):
    """
    **Status**: 416 Range Not Satisfiable
    """

    status_code = 416
    quiet = True


class PyFileError(Exception):
    def __init__(self, file):
        super().__init__("could not execute config file %s", file)


class Unauthorized(SanicException):
    """
    **Status**: 401 Unauthorized

    :param message: Message describing the exception.
    :param status_code: HTTP Status code.
    :param scheme: Name of the authentication scheme to be used.

    When present, kwargs is used to complete the WWW-Authentication header.

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
    """

    status_code = 401
    quiet = True

    def __init__(self, message, status_code=None, scheme=None, **kwargs):
        super().__init__(message, status_code)

        # if auth-scheme is specified, set "WWW-Authenticate" header
        if scheme is not None:
            values = ['{!s}="{!s}"'.format(k, v) for k, v in kwargs.items()]
            challenge = ", ".join(values)

            self.headers = {
                "WWW-Authenticate": f"{scheme} {challenge}".rstrip()
            }


class LoadFileException(SanicException):
    pass


class InvalidSignal(SanicException):
    pass


class WebsocketClosed(SanicException):
    quiet = True
    message = "Client has closed the websocket connection"
