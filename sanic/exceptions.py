from sanic.response import ALL_STATUS_CODES, COMMON_STATUS_CODES

TRACEBACK_STYLE = '''
    <style>
        body {
            padding: 20px;
            font-family: Arial, sans-serif;
        }

        p {
            margin: 0;
        }

        .summary {
            padding: 10px;
        }

        h1 {
            margin-bottom: 0;
        }

        h3 {
            margin-top: 10px;
        }

        h3 code {
            font-size: 24px;
        }

        .frame-line > * {
            padding: 5px 10px;
        }

        .frame-line {
            margin-bottom: 5px;
        }

        .frame-code {
            font-size: 16px;
            padding-left: 30px;
        }

        .tb-wrapper {
            border: 1px solid #f3f3f3;
        }

        .tb-header {
            background-color: #f3f3f3;
            padding: 5px 10px;
        }

        .tb-border {
            padding-top: 20px;
        }

        .frame-descriptor {
            background-color: #e2eafb;
        }

        .frame-descriptor {
            font-size: 14px;
        }
    </style>
'''

TRACEBACK_WRAPPER_HTML = '''
    <html>
        <head>
            {style}
        </head>
        <body>
            {inner_html}
            <div class="summary">
                <p>
                <b>{exc_name}: {exc_value}</b>
                    while handling path <code>{path}</code>
                </p>
            </div>
        </body>
    </html>
'''

TRACEBACK_WRAPPER_INNER_HTML = '''
    <h1>{exc_name}</h1>
    <h3><code>{exc_value}</code></h3>
    <div class="tb-wrapper">
        <p class="tb-header">Traceback (most recent call last):</p>
        {frame_html}
    </div>
'''

TRACEBACK_BORDER = '''
    <div class="tb-border">
        <b><i>
            The above exception was the direct cause of the
            following exception:
        </i></b>
    </div>
'''

TRACEBACK_LINE_HTML = '''
    <div class="frame-line">
        <p class="frame-descriptor">
            File {0.filename}, line <i>{0.lineno}</i>,
            in <code><b>{0.name}</b></code>
        </p>
        <p class="frame-code"><code>{0.line}</code></p>
    </div>
'''

INTERNAL_SERVER_ERROR_HTML = '''
    <h1>Internal Server Error</h1>
    <p>
        The server encountered an internal error and cannot complete
        your request.
    </p>
'''


_sanic_exceptions = {}


def add_status_code(code):
    """
    Decorator used for adding exceptions to _sanic_exceptions.
    """
    def class_decorator(cls):
        cls.status_code = code
        _sanic_exceptions[code] = cls
        return cls
    return class_decorator


class SanicException(Exception):

    def __init__(self, message, status_code=None):
        super().__init__(message)

        if status_code is not None:
            self.status_code = status_code


@add_status_code(404)
class NotFound(SanicException):
    pass


@add_status_code(400)
class InvalidUsage(SanicException):
    pass


@add_status_code(500)
class ServerError(SanicException):
    pass


class URLBuildError(ServerError):
    pass


class FileNotFound(NotFound):
    pass

    def __init__(self, message, path, relative_url):
        super().__init__(message)
        self.path = path
        self.relative_url = relative_url


@add_status_code(408)
class RequestTimeout(SanicException):
    pass


@add_status_code(413)
class PayloadTooLarge(SanicException):
    pass


class HeaderNotFound(InvalidUsage):
    pass


@add_status_code(416)
class ContentRangeError(SanicException):
    pass

    def __init__(self, message, content_range):
        super().__init__(message)
        self.headers = {
            'Content-Type': 'text/plain',
            "Content-Range": "bytes */%s" % (content_range.total,)
        }


@add_status_code(403)
class Forbidden(SanicException):
    pass


class InvalidRangeType(ContentRangeError):
    pass


@add_status_code(401)
class Unauthorized(SanicException):
    """
    Unauthorized exception (401 HTTP status code).

    :param message: Message describing the exception.
    :param scheme: Name of the authentication scheme to be used.

    When present, kwargs is used to complete the WWW-Authentication header.

    Examples::

        # With a Basic auth-scheme, realm MUST be present:
        raise Unauthorized("Auth required.", "Basic", realm="Restricted Area")

        # With a Digest auth-scheme, things are a bit more complicated:
        raise Unauthorized("Auth required.",
                           "Digest",
                           realm="Restricted Area",
                           qop="auth, auth-int",
                           algorithm="MD5",
                           nonce="abcdef",
                           opaque="zyxwvu")

        # With a Bearer auth-scheme, realm is optional so you can write:
        raise Unauthorized("Auth required.", "Bearer")

        # or, if you want to specify the realm:
        raise Unauthorized("Auth required.", "Bearer", realm="Restricted Area")
    """
    def __init__(self, message, scheme, **kwargs):
        super().__init__(message)

        values = ["{!s}={!r}".format(k, v) for k, v in kwargs.items()]
        challenge = ', '.join(values)

        self.headers = {
            "WWW-Authenticate": "{} {}".format(scheme, challenge).rstrip()
        }


def abort(status_code, message=None):
    """
    Raise an exception based on SanicException. Returns the HTTP response
    message appropriate for the given status code, unless provided.

    :param status_code: The HTTP status code to return.
    :param message: The HTTP response body. Defaults to the messages
                    in response.py for the given status code.
    """
    if message is None:
        message = COMMON_STATUS_CODES.get(status_code,
                                          ALL_STATUS_CODES.get(status_code))
        # These are stored as bytes in the STATUS_CODES dict
        message = message.decode('utf8')
    sanic_exception = _sanic_exceptions.get(status_code, SanicException)
    raise sanic_exception(message=message, status_code=status_code)
