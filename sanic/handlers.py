import sys

from traceback import extract_tb, format_exc

from sanic.exceptions import (
    INTERNAL_SERVER_ERROR_HTML,
    TRACEBACK_BORDER,
    TRACEBACK_LINE_HTML,
    TRACEBACK_STYLE,
    TRACEBACK_WRAPPER_HTML,
    TRACEBACK_WRAPPER_INNER_HTML,
    ContentRangeError,
    HeaderNotFound,
    InvalidRangeType,
    SanicException,
)
from sanic.log import logger
from sanic.response import html, text


class ErrorHandler:
    """
    Provide :class:`sanic.app.Sanic` application with a mechanism to handle
    and process any and all uncaught exceptions in a way the application
    developer will set fit.

    This error handling framework is built into the core that can be extended
    by the developers to perform a wide range of tasks from recording the error
    stats to reporting them to an external service that can be used for
    realtime alerting system.

    """

    handlers = None
    cached_handlers = None
    _missing = object()

    def __init__(self):
        self.handlers = []
        self.cached_handlers = {}
        self.debug = False

    def _render_exception(self, exception):
        frames = extract_tb(exception.__traceback__)

        frame_html = []
        for frame in frames:
            frame_html.append(TRACEBACK_LINE_HTML.format(frame))

        return TRACEBACK_WRAPPER_INNER_HTML.format(
            exc_name=exception.__class__.__name__,
            exc_value=exception,
            frame_html="".join(frame_html),
        )

    def _render_traceback_html(self, exception, request):
        exc_type, exc_value, tb = sys.exc_info()
        exceptions = []

        while exc_value:
            exceptions.append(self._render_exception(exc_value))
            exc_value = exc_value.__cause__

        return TRACEBACK_WRAPPER_HTML.format(
            style=TRACEBACK_STYLE,
            exc_name=exception.__class__.__name__,
            exc_value=exception,
            inner_html=TRACEBACK_BORDER.join(reversed(exceptions)),
            path=request.path,
        )

    def add(self, exception, handler):
        """
        Add a new exception handler to an already existing handler object.

        :param exception: Type of exception that need to be handled
        :param handler: Reference to the method that will handle the exception

        :type exception: :class:`sanic.exceptions.SanicException` or
            :class:`Exception`
        :type handler: ``function``

        :return: None
        """
        self.handlers.append((exception, handler))

    def lookup(self, exception):
        """
        Lookup the existing instance of :class:`ErrorHandler` and fetch the
        registered handler for a specific type of exception.

        This method leverages a dict lookup to speedup the retrieval process.

        :param exception: Type of exception

        :type exception: :class:`sanic.exceptions.SanicException` or
            :class:`Exception`

        :return: Registered function if found ``None`` otherwise
        """
        handler = self.cached_handlers.get(type(exception), self._missing)
        if handler is self._missing:
            for exception_class, handler in self.handlers:
                if isinstance(exception, exception_class):
                    self.cached_handlers[type(exception)] = handler
                    return handler
            self.cached_handlers[type(exception)] = None
            handler = None
        return handler

    def response(self, request, exception):
        """Fetches and executes an exception handler and returns a response
        object

        :param request: Instance of :class:`sanic.request.Request`
        :param exception: Exception to handle

        :type request: :class:`sanic.request.Request`
        :type exception: :class:`sanic.exceptions.SanicException` or
            :class:`Exception`

        :return: Wrap the return value obtained from :func:`default`
            or registered handler for that type of exception.
        """
        handler = self.lookup(exception)
        response = None
        try:
            if handler:
                response = handler(request, exception)
            if response is None:
                response = self.default(request, exception)
        except Exception:
            self.log(format_exc())
            try:
                url = repr(request.url)
            except AttributeError:
                url = "unknown"
            response_message = (
                "Exception raised in exception handler " '"%s" for uri: %s'
            )
            logger.exception(response_message, handler.__name__, url)

            if self.debug:
                return text(response_message % (handler.__name__, url), 500)
            else:
                return text("An error occurred while handling an error", 500)
        return response

    def log(self, message, level="error"):
        """
        Deprecated, do not use.
        """

    def default(self, request, exception):
        """
        Provide a default behavior for the objects of :class:`ErrorHandler`.
        If a developer chooses to extent the :class:`ErrorHandler` they can
        provide a custom implementation for this method to behave in a way
        they see fit.

        :param request: Incoming request
        :param exception: Exception object

        :type request: :class:`sanic.request.Request`
        :type exception: :class:`sanic.exceptions.SanicException` or
            :class:`Exception`
        :return:
        """
        self.log(format_exc())
        try:
            url = repr(request.url)
        except AttributeError:
            url = "unknown"

        response_message = "Exception occurred while handling uri: %s"
        logger.exception(response_message, url)

        if issubclass(type(exception), SanicException):
            return text(
                "Error: {}".format(exception),
                status=getattr(exception, "status_code", 500),
                headers=getattr(exception, "headers", dict()),
            )
        elif self.debug:
            html_output = self._render_traceback_html(exception, request)

            return html(html_output, status=500)
        else:
            return html(INTERNAL_SERVER_ERROR_HTML, status=500)


class ContentRangeHandler:
    """
    A mechanism to parse and process the incoming request headers to
    extract the content range information.

    :param request: Incoming api request
    :param stats: Stats related to the content

    :type request: :class:`sanic.request.Request`
    :type stats: :class:`posix.stat_result`

    :ivar start: Content Range start
    :ivar end: Content Range end
    :ivar size: Length of the content
    :ivar total: Total size identified by the :class:`posix.stat_result`
        instance
    :ivar ContentRangeHandler.headers: Content range header ``dict``
    """

    __slots__ = ("start", "end", "size", "total", "headers")

    def __init__(self, request, stats):
        self.total = stats.st_size
        _range = request.headers.get("Range")
        if _range is None:
            raise HeaderNotFound("Range Header Not Found")
        unit, _, value = tuple(map(str.strip, _range.partition("=")))
        if unit != "bytes":
            raise InvalidRangeType(
                "%s is not a valid Range Type" % (unit,), self
            )
        start_b, _, end_b = tuple(map(str.strip, value.partition("-")))
        try:
            self.start = int(start_b) if start_b else None
        except ValueError:
            raise ContentRangeError(
                "'%s' is invalid for Content Range" % (start_b,), self
            )
        try:
            self.end = int(end_b) if end_b else None
        except ValueError:
            raise ContentRangeError(
                "'%s' is invalid for Content Range" % (end_b,), self
            )
        if self.end is None:
            if self.start is None:
                raise ContentRangeError(
                    "Invalid for Content Range parameters", self
                )
            else:
                # this case represents `Content-Range: bytes 5-`
                self.end = self.total - 1
        else:
            if self.start is None:
                # this case represents `Content-Range: bytes -5`
                self.start = self.total - self.end
                self.end = self.total - 1
        if self.start >= self.end:
            raise ContentRangeError(
                "Invalid for Content Range parameters", self
            )
        self.size = self.end - self.start + 1
        self.headers = {
            "Content-Range": "bytes %s-%s/%s"
            % (self.start, self.end, self.total)
        }

    def __bool__(self):
        return self.size > 0
