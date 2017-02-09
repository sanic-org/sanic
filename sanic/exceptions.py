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


class URLBuildError(SanicException):
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


class HeaderNotFound(SanicException):
    status_code = 400


class ContentRangeError(SanicException):
    status_code = 416

    def __init__(self, message, content_range):
        super().__init__(message)
        self.headers = {
            'Content-Type': 'text/plain',
            "Content-Range": "bytes */%s" % (content_range.total,)
        }


class InvalidRangeType(ContentRangeError):
    pass
