import sys
from traceback import format_exc, extract_tb

from sanic.exceptions import (
    ContentRangeError,
    HeaderNotFound,
    INTERNAL_SERVER_ERROR_HTML,
    InvalidRangeType,
    SanicException,
    TRACEBACK_LINE_HTML,
    TRACEBACK_STYLE,
    TRACEBACK_WRAPPER_HTML,
    TRACEBACK_WRAPPER_INNER_HTML,
    TRACEBACK_BORDER)
from sanic.log import log
from sanic.response import text, html


class ErrorHandler:
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
            frame_html=''.join(frame_html))

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
            path=request.path)

    def add(self, exception, handler):
        self.handlers.append((exception, handler))

    def lookup(self, exception):
        handler = self.cached_handlers.get(exception, self._missing)
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

        :param request: Request
        :param exception: Exception to handle
        :return: Response object
        """
        handler = self.lookup(exception)
        response = None
        try:
            if handler:
                response = handler(request=request, exception=exception)
            if response is None:
                response = self.default(request=request, exception=exception)
        except Exception:
            self.log(format_exc())
            if self.debug:
                url = getattr(request, 'url', 'unknown')
                response_message = (
                    'Exception raised in exception handler "{}" '
                    'for uri: "{}"\n{}').format(
                        handler.__name__, url, format_exc())
                log.error(response_message)
                return text(response_message, 500)
            else:
                return text('An error occurred while handling an error', 500)
        return response

    def log(self, message, level='error'):
        """
        Override this method in an ErrorHandler subclass to prevent
        logging exceptions.
        """
        getattr(log, level)(message)

    def default(self, request, exception):
        self.log(format_exc())
        if issubclass(type(exception), SanicException):
            return text(
                'Error: {}'.format(exception),
                status=getattr(exception, 'status_code', 500),
                headers=getattr(exception, 'headers', dict())
            )
        elif self.debug:
            html_output = self._render_traceback_html(exception, request)

            response_message = (
                'Exception occurred while handling uri: "{}"\n{}'.format(
                    request.url, format_exc()))
            log.error(response_message)
            return html(html_output, status=500)
        else:
            return html(INTERNAL_SERVER_ERROR_HTML, status=500)


class ContentRangeHandler:
    """Class responsible for parsing request header"""
    __slots__ = ('start', 'end', 'size', 'total', 'headers')

    def __init__(self, request, stats):
        self.total = stats.st_size
        _range = request.headers.get('Range')
        if _range is None:
            raise HeaderNotFound('Range Header Not Found')
        unit, _, value = tuple(map(str.strip, _range.partition('=')))
        if unit != 'bytes':
            raise InvalidRangeType(
                '%s is not a valid Range Type' % (unit,), self)
        start_b, _, end_b = tuple(map(str.strip, value.partition('-')))
        try:
            self.start = int(start_b) if start_b else None
        except ValueError:
            raise ContentRangeError(
                '\'%s\' is invalid for Content Range' % (start_b,), self)
        try:
            self.end = int(end_b) if end_b else None
        except ValueError:
            raise ContentRangeError(
                '\'%s\' is invalid for Content Range' % (end_b,), self)
        if self.end is None:
            if self.start is None:
                raise ContentRangeError(
                    'Invalid for Content Range parameters', self)
            else:
                # this case represents `Content-Range: bytes 5-`
                self.end = self.total
        else:
            if self.start is None:
                # this case represents `Content-Range: bytes -5`
                self.start = self.total - self.end
                self.end = self.total
        if self.start >= self.end:
            raise ContentRangeError(
                'Invalid for Content Range parameters', self)
        self.size = self.end - self.start
        self.headers = {
            'Content-Range': "bytes %s-%s/%s" % (
                self.start, self.end, self.total)}

    def __bool__(self):
        return self.size > 0
