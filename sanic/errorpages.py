import sys

from traceback import extract_tb, format_exc

from sanic.exceptions import SanicException
from sanic.helpers import STATUS_CODES
from sanic.response import html


# Here, There Be Dragons (custom HTML formatting to follow)


def escape(text):
    """Minimal HTML escaping, not for attribute values (unlike html.escape)."""
    return f"{text}".replace("&", "&amp;").replace("<", "&lt;")


def exception_response(request, exception, debug):
    status = 500
    text = (
        "The server encountered an internal error "
        "and cannot complete your request."
    )

    headers = {}
    if isinstance(exception, SanicException):
        text = f"{exception}"
        status = getattr(exception, "status_code", status)
        headers = getattr(exception, "headers", headers)
    elif debug:
        text = f"{exception}"

    if debug:
        return html(_render_traceback_html(exception, request), status=status)

    # Keeping it minimal with trailing newline for pretty curl/console output
    status_text = STATUS_CODES.get(status).decode() or "Error Occurred"
    title = escape(f"{status} — {status_text}")
    text = escape(text)
    return html(
        f"<!DOCTYPE html><title>{title}</title><h1>⚠️ {title}</h1><p>{text}\n",
        status=status,
        headers=headers,
    )


def _render_exception(exception):
    frames = extract_tb(exception.__traceback__)

    frame_html = []
    for frame in frames:
        frame_html.append(TRACEBACK_LINE_HTML.format(frame))

    return TRACEBACK_WRAPPER_INNER_HTML.format(
        exc_name=escape(exception.__class__.__name__),
        exc_value=escape(exception),
        frame_html="".join(frame_html),
    )


def _render_traceback_html(exception, request):
    exc_type, exc_value, tb = sys.exc_info()
    exceptions = []

    while exc_value:
        exceptions.append(_render_exception(exc_value))
        exc_value = exc_value.__cause__

    return TRACEBACK_WRAPPER_HTML.format(
        style=TRACEBACK_STYLE,
        exc_name=escape(exception.__class__.__name__),
        exc_value=escape(exception),
        inner_html=TRACEBACK_BORDER.join(reversed(exceptions)),
        path=escape(request.path),
    )


TRACEBACK_STYLE = """
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
"""

TRACEBACK_WRAPPER_HTML = """
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
"""

TRACEBACK_WRAPPER_INNER_HTML = """
    <h1>{exc_name}</h1>
    <h3><code>{exc_value}</code></h3>
    <div class="tb-wrapper">
        <p class="tb-header">Traceback (most recent call last):</p>
        {frame_html}
    </div>
"""

TRACEBACK_BORDER = """
    <div class="tb-border">
        <b><i>
            The above exception was the direct cause of the
            following exception:
        </i></b>
    </div>
"""

TRACEBACK_LINE_HTML = """
    <div class="frame-line">
        <p class="frame-descriptor">
            File {0.filename}, line <i>{0.lineno}</i>,
            in <code><b>{0.name}</b></code>
        </p>
        <p class="frame-code"><code>{0.line}</code></p>
    </div>
"""
