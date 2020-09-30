import sys
import typing as t

from functools import partial
from traceback import extract_tb

from sanic.exceptions import InvalidUsage, SanicException
from sanic.helpers import STATUS_CODES
from sanic.request import Request
from sanic.response import HTTPResponse, html, json, text


try:
    from ujson import dumps

    dumps = partial(dumps, escape_forward_slashes=False)
except ImportError:  # noqa
    from json import dumps  # type: ignore


FALLBACK_TEXT = (
    "The server encountered an internal error and "
    "cannot complete your request."
)
FALLBACK_STATUS = 500


class BaseRenderer:
    def __init__(self, request, exception, debug):
        self.request = request
        self.exception = exception
        self.debug = debug

    @property
    def headers(self):
        if isinstance(self.exception, SanicException):
            return getattr(self.exception, "headers", {})
        return {}

    @property
    def status(self):
        if isinstance(self.exception, SanicException):
            return getattr(self.exception, "status_code", FALLBACK_STATUS)
        return FALLBACK_STATUS

    @property
    def text(self):
        if self.debug or isinstance(self.exception, SanicException):
            return str(self.exception)
        return FALLBACK_TEXT

    @property
    def title(self):
        status_text = STATUS_CODES.get(self.status, b"Error Occurred").decode()
        return f"{self.status} — {status_text}"

    def render(self):
        output = (
            self.full
            if self.debug and not getattr(self.exception, "quiet", False)
            else self.minimal
        )
        return output()

    def minimal(self):  # noqa
        raise NotImplementedError

    def full(self):  # noqa
        raise NotImplementedError


class HTMLRenderer(BaseRenderer):
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
    OUTPUT_HTML = (
        "<!DOCTYPE html><html lang=en>"
        "<meta charset=UTF-8><title>{title}</title>\n"
        "<style>{style}</style>\n"
        "<h1>{title}</h1><p>{text}\n"
        "{body}"
    )

    def full(self):
        return html(
            self.OUTPUT_HTML.format(
                title=self.title,
                text=self.text,
                style=self.TRACEBACK_STYLE,
                body=self._generate_body(),
            ),
            status=self.status,
        )

    def minimal(self):
        return html(
            self.OUTPUT_HTML.format(
                title=self.title,
                text=self.text,
                style=self.TRACEBACK_STYLE,
                body="",
            ),
            status=self.status,
            headers=self.headers,
        )

    @property
    def text(self):
        return escape(super().text)

    @property
    def title(self):
        return escape(f"⚠️ {super().title}")

    def _generate_body(self):
        _, exc_value, __ = sys.exc_info()
        exceptions = []
        while exc_value:
            exceptions.append(self._format_exc(exc_value))
            exc_value = exc_value.__cause__

        traceback_html = self.TRACEBACK_BORDER.join(reversed(exceptions))
        appname = escape(self.request.app.name)
        name = escape(self.exception.__class__.__name__)
        value = escape(self.exception)
        path = escape(self.request.path)
        lines = [
            f"<h2>Traceback of {appname} (most recent call last):</h2>",
            f"{traceback_html}",
            "<div class=summary><p>",
            f"<b>{name}: {value}</b> while handling path <code>{path}</code>",
            "</div>",
        ]
        return "\n".join(lines)

    def _format_exc(self, exc):
        frames = extract_tb(exc.__traceback__)
        frame_html = "".join(
            self.TRACEBACK_LINE_HTML.format(frame) for frame in frames
        )
        return self.TRACEBACK_WRAPPER_HTML.format(
            exc_name=escape(exc.__class__.__name__),
            exc_value=escape(exc),
            frame_html=frame_html,
        )


class TextRenderer(BaseRenderer):
    OUTPUT_TEXT = "{title}\n{bar}\n{text}\n\n{body}"
    SPACER = "  "

    def full(self):
        return text(
            self.OUTPUT_TEXT.format(
                title=self.title,
                text=self.text,
                bar=("=" * len(self.title)),
                body=self._generate_body(),
            ),
            status=self.status,
        )

    def minimal(self):
        return text(
            self.OUTPUT_TEXT.format(
                title=self.title,
                text=self.text,
                bar=("=" * len(self.title)),
                body="",
            ),
            status=self.status,
            headers=self.headers,
        )

    @property
    def title(self):
        return f"⚠️ {super().title}"

    def _generate_body(self):
        _, exc_value, __ = sys.exc_info()
        exceptions = []

        # traceback_html = self.TRACEBACK_BORDER.join(reversed(exceptions))
        lines = [
            f"{self.exception.__class__.__name__}: {self.exception} while "
            f"handling path {self.request.path}",
            f"Traceback of {self.request.app.name} (most recent call last):\n",
        ]

        while exc_value:
            exceptions.append(self._format_exc(exc_value))
            exc_value = exc_value.__cause__

        return "\n".join(lines + exceptions[::-1])

    def _format_exc(self, exc):
        frames = "\n\n".join(
            [
                f"{self.SPACER * 2}File {frame.filename}, "
                f"line {frame.lineno}, in "
                f"{frame.name}\n{self.SPACER * 2}{frame.line}"
                for frame in extract_tb(exc.__traceback__)
            ]
        )
        return f"{self.SPACER}{exc.__class__.__name__}: {exc}\n{frames}"


class JSONRenderer(BaseRenderer):
    def full(self):
        output = self._generate_output(full=True)
        return json(output, status=self.status, dumps=dumps)

    def minimal(self):
        output = self._generate_output(full=False)
        return json(output, status=self.status, dumps=dumps)

    def _generate_output(self, *, full):
        output = {
            "description": self.title,
            "status": self.status,
            "message": self.text,
        }

        if full:
            _, exc_value, __ = sys.exc_info()
            exceptions = []

            while exc_value:
                exceptions.append(
                    {
                        "type": exc_value.__class__.__name__,
                        "exception": str(exc_value),
                        "frames": [
                            {
                                "file": frame.filename,
                                "line": frame.lineno,
                                "name": frame.name,
                                "src": frame.line,
                            }
                            for frame in extract_tb(exc_value.__traceback__)
                        ],
                    }
                )
                exc_value = exc_value.__cause__

            output["path"] = self.request.path
            output["args"] = self.request.args
            output["exceptions"] = exceptions[::-1]

        return output

    @property
    def title(self):
        return STATUS_CODES.get(self.status, b"Error Occurred").decode()


def escape(text):
    """Minimal HTML escaping, not for attribute values (unlike html.escape)."""
    return f"{text}".replace("&", "&amp;").replace("<", "&lt;")


RENDERERS_BY_CONFIG = {
    "html": HTMLRenderer,
    "json": JSONRenderer,
    "text": TextRenderer,
}

RENDERERS_BY_CONTENT_TYPE = {
    "multipart/form-data": HTMLRenderer,
    "application/json": JSONRenderer,
    "text/plain": TextRenderer,
}


def exception_response(
    request: Request,
    exception: Exception,
    debug: bool,
    renderer: t.Type[t.Optional[BaseRenderer]] = None,
) -> HTTPResponse:
    """Render a response for the default FALLBACK exception handler"""

    if not renderer:
        renderer = HTMLRenderer

        if request:
            if request.app.config.FALLBACK_ERROR_FORMAT == "auto":
                try:
                    renderer = JSONRenderer if request.json else HTMLRenderer
                except InvalidUsage:
                    renderer = HTMLRenderer

                content_type, *_ = request.headers.get(
                    "content-type", ""
                ).split(";")
                renderer = RENDERERS_BY_CONTENT_TYPE.get(
                    content_type, renderer
                )
            else:
                render_format = request.app.config.FALLBACK_ERROR_FORMAT
                renderer = RENDERERS_BY_CONFIG.get(render_format, renderer)

    renderer = t.cast(t.Type[BaseRenderer], renderer)
    return renderer(request, exception, debug).render()
