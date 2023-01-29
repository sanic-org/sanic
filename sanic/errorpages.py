"""
Sanic `provides a pattern
<https://sanicframework.org/guide/best-practices/exceptions.html#using-sanic-exceptions>`_
for providing a response when an exception occurs. However, if you do no handle
an exception, it will provide a fallback. There are three fallback types:

- HTML - *default*
- Text
- JSON

Setting ``app.config.FALLBACK_ERROR_FORMAT = "auto"`` will enable a switch that
will attempt to provide an appropriate response format based upon the
request type.
"""

import sys
import typing as t

from functools import partial
from traceback import extract_tb

from sanic.exceptions import BadRequest, SanicException
from sanic.helpers import STATUS_CODES
from sanic.request import Request
from sanic.response import HTTPResponse, html, json, text


dumps: t.Callable[..., str]
try:
    from ujson import dumps

    dumps = partial(dumps, escape_forward_slashes=False)
except ImportError:  # noqa
    from json import dumps


DEFAULT_FORMAT = "auto"
FALLBACK_TEXT = (
    "The server encountered an internal error and "
    "cannot complete your request."
)
FALLBACK_STATUS = 500


class BaseRenderer:
    """
    Base class that all renderers must inherit from.
    """

    dumps = staticmethod(dumps)

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

    def render(self) -> HTTPResponse:
        """
        Outputs the exception as a :class:`HTTPResponse`.

        :return: The formatted exception
        :rtype: str
        """
        output = (
            self.full
            if self.debug and not getattr(self.exception, "quiet", False)
            else self.minimal
        )
        return output()

    def minimal(self) -> HTTPResponse:  # noqa
        """
        Provide a formatted message that is meant to not show any sensitive
        data or details.
        """
        raise NotImplementedError

    def full(self) -> HTTPResponse:  # noqa
        """
        Provide a formatted message that has all details and is mean to be used
        primarily for debugging and non-production environments.
        """
        raise NotImplementedError


class HTMLRenderer(BaseRenderer):
    """
    Render an exception as HTML.

    The default fallback type.
    """

    TRACEBACK_STYLE = """
        html { font-family: sans-serif }
        h2 { color: #888; }
        .tb-wrapper p, dl, dd { margin: 0 }
        .frame-border { margin: 1rem }
        .frame-line > *, dt, dd { padding: 0.3rem 0.6rem }
        .frame-line, dl { margin-bottom: 0.3rem }
        .frame-code, dd { font-size: 16px; padding-left: 4ch }
        .tb-wrapper, dl { border: 1px solid #eee }
        .tb-header,.obj-header {
            background: #eee; padding: 0.3rem; font-weight: bold
        }
        .frame-descriptor, dt { background: #e2eafb; font-size: 14px }
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
    OBJECT_WRAPPER_HTML = (
        "<div class=obj-header>{title}</div>"
        "<dl class={obj_type}>{display_html}</dl>"
    )
    OBJECT_DISPLAY_HTML = "<dt>{key}</dt><dd><code>{value}</code></dd>"
    OUTPUT_HTML = (
        "<!DOCTYPE html><html lang=en>"
        "<meta charset=UTF-8><title>{title}</title>\n"
        "<style>{style}</style>\n"
        "<h1>{title}</h1><p>{text}\n"
        "{body}"
    )

    def full(self) -> HTTPResponse:
        return html(
            self.OUTPUT_HTML.format(
                title=self.title,
                text=self.text,
                style=self.TRACEBACK_STYLE,
                body=self._generate_body(full=True),
            ),
            status=self.status,
        )

    def minimal(self) -> HTTPResponse:
        return html(
            self.OUTPUT_HTML.format(
                title=self.title,
                text=self.text,
                style=self.TRACEBACK_STYLE,
                body=self._generate_body(full=False),
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

    def _generate_body(self, *, full):
        lines = []
        if full:
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
            lines += [
                f"<h2>Traceback of {appname} " "(most recent call last):</h2>",
                f"{traceback_html}",
                "<div class=summary><p>",
                f"<b>{name}: {value}</b> "
                f"while handling path <code>{path}</code>",
                "</div>",
            ]

        for attr, display in (("context", True), ("extra", bool(full))):
            info = getattr(self.exception, attr, None)
            if info and display:
                lines.append(self._generate_object_display(info, attr))

        return "\n".join(lines)

    def _generate_object_display(
        self, obj: t.Dict[str, t.Any], descriptor: str
    ) -> str:
        display = "".join(
            self.OBJECT_DISPLAY_HTML.format(key=key, value=value)
            for key, value in obj.items()
        )
        return self.OBJECT_WRAPPER_HTML.format(
            title=descriptor.title(),
            display_html=display,
            obj_type=descriptor.lower(),
        )

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
    """
    Render an exception as plain text.
    """

    OUTPUT_TEXT = "{title}\n{bar}\n{text}\n\n{body}"
    SPACER = "  "

    def full(self) -> HTTPResponse:
        return text(
            self.OUTPUT_TEXT.format(
                title=self.title,
                text=self.text,
                bar=("=" * len(self.title)),
                body=self._generate_body(full=True),
            ),
            status=self.status,
        )

    def minimal(self) -> HTTPResponse:
        return text(
            self.OUTPUT_TEXT.format(
                title=self.title,
                text=self.text,
                bar=("=" * len(self.title)),
                body=self._generate_body(full=False),
            ),
            status=self.status,
            headers=self.headers,
        )

    @property
    def title(self):
        return f"⚠️ {super().title}"

    def _generate_body(self, *, full):
        lines = []
        if full:
            _, exc_value, __ = sys.exc_info()
            exceptions = []

            lines += [
                f"{self.exception.__class__.__name__}: {self.exception} while "
                f"handling path {self.request.path}",
                f"Traceback of {self.request.app.name} "
                "(most recent call last):\n",
            ]

            while exc_value:
                exceptions.append(self._format_exc(exc_value))
                exc_value = exc_value.__cause__

            lines += exceptions[::-1]

        for attr, display in (("context", True), ("extra", bool(full))):
            info = getattr(self.exception, attr, None)
            if info and display:
                lines += self._generate_object_display_list(info, attr)

        return "\n".join(lines)

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

    def _generate_object_display_list(self, obj, descriptor):
        lines = [f"\n{descriptor.title()}"]
        for key, value in obj.items():
            display = self.dumps(value)
            lines.append(f"{self.SPACER * 2}{key}: {display}")
        return lines


class JSONRenderer(BaseRenderer):
    """
    Render an exception as JSON.
    """

    def full(self) -> HTTPResponse:
        output = self._generate_output(full=True)
        return json(output, status=self.status, dumps=self.dumps)

    def minimal(self) -> HTTPResponse:
        output = self._generate_output(full=False)
        return json(output, status=self.status, dumps=self.dumps)

    def _generate_output(self, *, full):
        output = {
            "description": self.title,
            "status": self.status,
            "message": self.text,
        }

        for attr, display in (("context", True), ("extra", bool(full))):
            info = getattr(self.exception, attr, None)
            if info and display:
                output[attr] = info

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
    """
    Minimal HTML escaping, not for attribute values (unlike html.escape).
    """
    return f"{text}".replace("&", "&amp;").replace("<", "&lt;")


RENDERERS_BY_CONFIG = {
    "html": HTMLRenderer,
    "json": JSONRenderer,
    "text": TextRenderer,
}

RENDERERS_BY_CONTENT_TYPE = {
    "text/plain": TextRenderer,
    "application/json": JSONRenderer,
    "multipart/form-data": HTMLRenderer,
    "text/html": HTMLRenderer,
}
CONTENT_TYPE_BY_RENDERERS = {
    v: k for k, v in RENDERERS_BY_CONTENT_TYPE.items()
}

RESPONSE_MAPPING = {
    "empty": "html",
    "json": "json",
    "text": "text",
    "raw": "text",
    "html": "html",
    "file": "html",
    "file_stream": "text",
    "stream": "text",
    "redirect": "html",
    "text/plain": "text",
    "text/html": "html",
    "application/json": "json",
}


def check_error_format(format):
    if format not in RENDERERS_BY_CONFIG and format != "auto":
        raise SanicException(f"Unknown format: {format}")


def exception_response(
    request: Request,
    exception: Exception,
    debug: bool,
    fallback: str,
    base: t.Type[BaseRenderer],
    renderer: t.Type[t.Optional[BaseRenderer]] = None,
) -> HTTPResponse:
    """
    Render a response for the default FALLBACK exception handler.
    """
    content_type = None

    if not renderer:
        # Make sure we have something set
        renderer = base
        render_format = fallback

        if request:
            # If there is a request, try and get the format
            # from the route
            if request.route:
                try:
                    if request.route.extra.error_format:
                        render_format = request.route.extra.error_format
                except AttributeError:
                    ...

            content_type = request.headers.getone("content-type", "").split(
                ";"
            )[0]

            acceptable = request.accept

            # If the format is auto still, make a guess
            if render_format == "auto":
                # First, if there is an Accept header, check if text/html
                # is the first option
                # According to MDN Web Docs, all major browsers use text/html
                # as the primary value in Accept (with the exception of IE 8,
                # and, well, if you are supporting IE 8, then you have bigger
                # problems to concern yourself with than what default exception
                # renderer is used)
                # Source:
                # https://developer.mozilla.org/en-US/docs/Web/HTTP/Content_negotiation/List_of_default_Accept_values

                if acceptable and acceptable[0].match(
                    "text/html",
                    allow_type_wildcard=False,
                    allow_subtype_wildcard=False,
                ):
                    renderer = HTMLRenderer

                # Second, if there is an Accept header, check if
                # application/json is an option, or if the content-type
                # is application/json
                elif (
                    acceptable
                    and acceptable.match(
                        "application/json",
                        allow_type_wildcard=False,
                        allow_subtype_wildcard=False,
                    )
                    or content_type == "application/json"
                ):
                    renderer = JSONRenderer

                # Third, if there is no Accept header, assume we want text.
                # The likely use case here is a raw socket.
                elif not acceptable:
                    renderer = TextRenderer
                else:
                    # Fourth, look to see if there was a JSON body
                    # When in this situation, the request is probably coming
                    # from curl, an API client like Postman or Insomnia, or a
                    # package like requests or httpx
                    try:
                        # Give them the benefit of the doubt if they did:
                        # $ curl localhost:8000 -d '{"foo": "bar"}'
                        # And provide them with JSONRenderer
                        renderer = JSONRenderer if request.json else base
                    except BadRequest:
                        renderer = base
            else:
                renderer = RENDERERS_BY_CONFIG.get(render_format, renderer)

            # Lastly, if there is an Accept header, make sure
            # our choice is okay
            if acceptable:
                type_ = CONTENT_TYPE_BY_RENDERERS.get(renderer)  # type: ignore
                if type_ and type_ not in acceptable:
                    # If the renderer selected is not in the Accept header
                    # look through what is in the Accept header, and select
                    # the first option that matches. Otherwise, just drop back
                    # to the original default
                    for accept in acceptable:
                        mtype = f"{accept.type_}/{accept.subtype}"
                        maybe = RENDERERS_BY_CONTENT_TYPE.get(mtype)
                        if maybe:
                            renderer = maybe
                            break
                    else:
                        renderer = base

    renderer = t.cast(t.Type[BaseRenderer], renderer)
    return renderer(request, exception, debug).render()
