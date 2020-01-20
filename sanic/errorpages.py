import sys

from traceback import extract_tb

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

    status_text = STATUS_CODES.get(status, b"Error Occurred").decode()
    title = escape(f"{status} — {status_text}")
    text = escape(text)

    if debug and not getattr(exception, "quiet", False):
        return html(
            f"<!DOCTYPE html><meta charset=UTF-8><title>{title}</title>"
            f"<style>{TRACEBACK_STYLE}</style>\n"
            f"<h1>⚠️ {title}</h1><p>{text}\n"
            f"{_render_traceback_html(request, exception)}",
            status=status,
        )

    # Keeping it minimal with trailing newline for pretty curl/console output
    return html(
        f"<!DOCTYPE html><meta charset=UTF-8><title>{title}</title>"
        "<style>html { font-family: sans-serif }</style>\n"
        f"<h1>⚠️ {title}</h1><p>{text}\n",
        status=status,
        headers=headers,
    )


def _render_exception(exception):
    frames = extract_tb(exception.__traceback__)
    frame_html = "".join(TRACEBACK_LINE_HTML.format(frame) for frame in frames)
    return TRACEBACK_WRAPPER_HTML.format(
        exc_name=escape(exception.__class__.__name__),
        exc_value=escape(exception),
        frame_html=frame_html,
    )


def _render_traceback_html(request, exception):
    exc_type, exc_value, tb = sys.exc_info()
    exceptions = []
    while exc_value:
        exceptions.append(_render_exception(exc_value))
        exc_value = exc_value.__cause__

    traceback_html = TRACEBACK_BORDER.join(reversed(exceptions))
    appname = escape(request.app.name)
    name = escape(exception.__class__.__name__)
    value = escape(exception)
    path = escape(request.path)
    return (
        f"<h2>Traceback of {appname} (most recent call last):</h2>"
        f"{traceback_html}"
        "<div class=summary><p>"
        f"<b>{name}: {value}</b> while handling path <code>{path}</code>"
    )


TRACEBACK_STYLE = """
    html { font-family: sans-serif }
    h2 { color: #888; }
    .tb-wrapper p { margin: 0 }
    .frame-border { margin: 1rem }
    .frame-line > * { padding: 0.3rem 0.6rem }
    .frame-line { margin-bottom: 0.3rem }
    .frame-code { font-size: 16px; padding-left: 4ch }
    .tb-wrapper { border: 1px solid #eee }
    .tb-header { background: #eee; padding: 0.3rem; font-weight: bold }
    .frame-descriptor { background: #e2eafb; font-size: 14px }
"""

TRACEBACK_WRAPPER_HTML = (
    "<div class=tb-header>{exc_name}: {exc_value}</div>"
    "<div class=tb-wrapper>{frame_html}</div>"
)

TRACEBACK_BORDER = (
    "<div class=frame-border>"
    "The above exception was the direct cause of the following exception:"
    "</div>"
)

TRACEBACK_LINE_HTML = (
    "<div class=frame-line>"
    "<p class=frame-descriptor>"
    "File {0.filename}, line <i>{0.lineno}</i>, "
    "in <code><b>{0.name}</b></code>"
    "<p class=frame-code><code>{0.line}</code>"
    "</div>"
)
