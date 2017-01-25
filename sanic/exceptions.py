from .response import text, html
from .log import log
from traceback import format_exc, extract_tb
import sys

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
            <h1>{exc_name}</h1>
            <h3><code>{exc_value}</code></h3>
            <div class="tb-wrapper">
                <p class="tb-header">Traceback (most recent call last):</p>
                {frame_html}
                <p class="summary">
                <b>{exc_name}: {exc_value}</b>
                    while handling uri <code>{uri}</code>
                </p>
            </div>
        </body>
    </html>
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


class SanicException(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code


class NotFound(SanicException):
    status_code = 404


class InvalidUsage(SanicException):
    status_code = 400


class ServerError(SanicException):
    status_code = 500


class FileNotFound(NotFound):
    status_code = 404

    def __init__(self, message, path, relative_url):
        super().__init__(message)
        self.path = path
        self.relative_url = relative_url


class RequestTimeout(SanicException):
    status_code = 408


class PayloadTooLarge(SanicException):
    status_code = 413


class Handler:
    handlers = None

    def __init__(self):
        self.handlers = {}
        self.debug = False

    def _render_traceback_html(self, exception, request):
        exc_type, exc_value, tb = sys.exc_info()
        frames = extract_tb(tb)

        frame_html = []
        for frame in frames:
            frame_html.append(TRACEBACK_LINE_HTML.format(frame))

        return TRACEBACK_WRAPPER_HTML.format(
            style=TRACEBACK_STYLE,
            exc_name=exc_type.__name__,
            exc_value=exc_value,
            frame_html=''.join(frame_html),
            uri=request.url)

    def add(self, exception, handler):
        self.handlers[exception] = handler

    def response(self, request, exception):
        """
        Fetches and executes an exception handler and returns a response object

        :param request: Request
        :param exception: Exception to handle
        :return: Response object
        """
        handler = self.handlers.get(type(exception), self.default)
        try:
            response = handler(request=request, exception=exception)
        except:
            log.error(format_exc())
            if self.debug:
                response_message = (
                    'Exception raised in exception handler "{}" '
                    'for uri: "{}"\n{}').format(
                        handler.__name__, request.url, format_exc())
                log.error(response_message)
                return text(response_message, 500)
            else:
                return text('An error occurred while handling an error', 500)
        return response

    def default(self, request, exception):
        log.error(format_exc())
        if issubclass(type(exception), SanicException):
            return text(
                'Error: {}'.format(exception),
                status=getattr(exception, 'status_code', 500))
        elif self.debug:
            html_output = self._render_traceback_html(exception, request)

            response_message = (
                'Exception occurred while handling uri: "{}"\n{}'.format(
                    request.url, format_exc()))
            log.error(response_message)
            return html(html_output, status=500)
        else:
            return html(INTERNAL_SERVER_ERROR_HTML, status=500)
