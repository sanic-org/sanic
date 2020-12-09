from sanic.helpers import STATUS_CODES


_sanic_exceptions = {}


def add_status_code(code, quiet=None):
    """
    Decorator used for adding exceptions to :class:`SanicException`.
    """

    def class_decorator(cls):
        cls.status_code = code
        if quiet or quiet is None and code != 500:
            cls.quiet = True
        _sanic_exceptions[code] = cls
        return cls

    return class_decorator


class SanicException(Exception):
    def __init__(self, message, status_code=None, quiet=None):
        super().__init__(message)

        if status_code is not None:
            self.status_code = status_code

        # quiet=None/False/True with None meaning choose by status
        if quiet or quiet is None and status_code not in (None, 500):
            self.quiet = True


@add_status_code(404)
class NotFound(SanicException):
    pass


@add_status_code(400)
class InvalidUsage(SanicException):
    pass


@add_status_code(405)
class MethodNotSupported(SanicException):
    def __init__(self, message, method, allowed_methods):
        super().__init__(message)
        self.headers = {"Allow": ", ".join(allowed_methods)}


@add_status_code(500)
class ServerError(SanicException):
    pass


@add_status_code(503)
class ServiceUnavailable(SanicException):
    """The server is currently unavailable (because it is overloaded or
    down for maintenance). Generally, this is a temporary state."""

    pass


class URLBuildError(ServerError):
    pass


class FileNotFound(NotFound):
    def __init__(self, message, path, relative_url):
        super().__init__(message)
        self.path = path
        self.relative_url = relative_url


@add_status_code(408)
class RequestTimeout(SanicException):
    """The Web server (running the Web site) thinks that there has been too
    long an interval of time between 1) the establishment of an IP
    connection (socket) between the client and the server and
    2) the receipt of any data on that socket, so the server has dropped
    the connection. The socket connection has actually been lost - the Web
    server has 'timed out' on that particular socket connection.
    """

    pass


@add_status_code(413)
class PayloadTooLarge(SanicException):
    pass


class HeaderNotFound(InvalidUsage):
    pass


@add_status_code(416)
class ContentRangeError(SanicException):
    def __init__(self, message, content_range):
        super().__init__(message)
        self.headers = {"Content-Range": f"bytes */{content_range.total}"}


@add_status_code(417)
class HeaderExpectationFailed(SanicException):
    pass


@add_status_code(403)
class Forbidden(SanicException):
    pass


class InvalidRangeType(ContentRangeError):
    pass


class PyFileError(Exception):
    def __init__(self, file):
        super().__init__("could not execute config file %s", file)


@add_status_code(401)
class Unauthorized(SanicException):
    """
    Unauthorized exception (401 HTTP status code).

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


def abort(status_code, message=None):
    """
    Raise an exception based on SanicException. Returns the HTTP response
    message appropriate for the given status code, unless provided.

    :param status_code: The HTTP status code to return.
    :param message: The HTTP response body. Defaults to the messages in
    STATUS_CODES from sanic.helpers for the given status code.
    """
    if message is None:
        message = STATUS_CODES.get(status_code)
        # These are stored as bytes in the STATUS_CODES dict
        message = message.decode("utf8")
    sanic_exception = _sanic_exceptions.get(status_code, SanicException)
    raise sanic_exception(message=message, status_code=status_code)
