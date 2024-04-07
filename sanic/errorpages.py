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

from __future__ import annotations

import sys
import typing as t

from functools import partial
from traceback import extract_tb

from sanic.exceptions import BadRequest, SanicException
from sanic.helpers import STATUS_CODES
from sanic.log import deprecation, logger
from sanic.pages.error import ErrorPage
from sanic.response import html, json, text


dumps: t.Callable[..., str]
try:
    from ujson import dumps

    dumps = partial(dumps, escape_forward_slashes=False)
except ImportError:  # noqa
    from json import dumps

if t.TYPE_CHECKING:
    from sanic import HTTPResponse, Request

DEFAULT_FORMAT = "auto"
FALLBACK_TEXT = """\
The application encountered an unexpected error and could not continue.\
"""
FALLBACK_STATUS = 500
JSON = "application/json"


class BaseRenderer:
    """Base class that all renderers must inherit from.

    This class defines the structure for rendering objects, handling the core functionality that specific renderers may extend.

    Attributes:
        request (Request): The incoming request object that needs rendering.
        exception (Exception): Any exception that occurred and needs to be rendered.
        debug (bool): Flag indicating whether to render with debugging information.

    Methods:
        dumps: A static method that must be overridden by subclasses to define the specific rendering.

    Args:
        request (Request): The incoming request object that needs rendering.
        exception (Exception): Any exception that occurred and needs to be rendered.
        debug (bool): Flag indicating whether to render with debugging information.
    """  # noqa: E501

    dumps = staticmethod(dumps)

    def __init__(self, request: Request, exception: Exception, debug: bool):
        self.request = request
        self.exception = exception
        self.debug = debug

    @property
    def headers(self) -> t.Dict[str, str]:
        """The headers to be used for the response."""
        if isinstance(self.exception, SanicException):
            return getattr(self.exception, "headers", {})
        return {}

    @property
    def status(self):
        """The status code to be used for the response."""
        if isinstance(self.exception, SanicException):
            return getattr(self.exception, "status_code", FALLBACK_STATUS)
        return FALLBACK_STATUS

    @property
    def text(self):
        """The text to be used for the response."""
        if self.debug or isinstance(self.exception, SanicException):
            return str(self.exception)
        return FALLBACK_TEXT

    @property
    def title(self):
        """The title to be used for the response."""
        status_text = STATUS_CODES.get(self.status, b"Error Occurred").decode()
        return f"{self.status} — {status_text}"

    def render(self) -> HTTPResponse:
        """Outputs the exception as a response.

        Returns:
            HTTPResponse: The response object.
        """
        output = (
            self.full
            if self.debug and not getattr(self.exception, "quiet", False)
            else self.minimal
        )()
        output.status = self.status
        output.headers.update(self.headers)
        return output

    def minimal(self) -> HTTPResponse:  # noqa
        """Provide a formatted message that is meant to not show any sensitive data or details.

        This is the default fallback for production environments.

        Returns:
            HTTPResponse: The response object.
        """  # noqa: E501
        raise NotImplementedError

    def full(self) -> HTTPResponse:  # noqa
        """Provide a formatted message that has all details and is mean to be used primarily for debugging and non-production environments.

        Returns:
            HTTPResponse: The response object.
        """  # noqa: E501
        raise NotImplementedError


class HTMLRenderer(BaseRenderer):
    """Render an exception as HTML.

    The default fallback type.
    """

    def full(self) -> HTTPResponse:
        page = ErrorPage(
            debug=self.debug,
            title=super().title,
            text=super().text,
            request=self.request,
            exc=self.exception,
        )
        return html(page.render())

    def minimal(self) -> HTTPResponse:
        return self.full()


class TextRenderer(BaseRenderer):
    """Render an exception as plain text."""

    OUTPUT_TEXT = "{title}\n{bar}\n{text}\n\n{body}"
    SPACER = "  "

    def full(self) -> HTTPResponse:
        return text(
            self.OUTPUT_TEXT.format(
                title=self.title,
                text=self.text,
                bar=("=" * len(self.title)),
                body=self._generate_body(full=True),
            )
        )

    def minimal(self) -> HTTPResponse:
        return text(
            self.OUTPUT_TEXT.format(
                title=self.title,
                text=self.text,
                bar=("=" * len(self.title)),
                body=self._generate_body(full=False),
            )
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
    """Render an exception as JSON."""

    def full(self) -> HTTPResponse:
        output = self._generate_output(full=True)
        return json(output, dumps=self.dumps)

    def minimal(self) -> HTTPResponse:
        output = self._generate_output(full=False)
        return json(output, dumps=self.dumps)

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
    """Minimal HTML escaping, not for attribute values (unlike html.escape)."""
    return f"{text}".replace("&", "&amp;").replace("<", "&lt;")


MIME_BY_CONFIG = {
    "text": "text/plain",
    "json": "application/json",
    "html": "text/html",
}
CONFIG_BY_MIME = {v: k for k, v in MIME_BY_CONFIG.items()}
RENDERERS_BY_CONTENT_TYPE = {
    "text/plain": TextRenderer,
    "application/json": JSONRenderer,
    "multipart/form-data": HTMLRenderer,
    "text/html": HTMLRenderer,
}

# Handler source code is checked for which response types it returns with the
# route error_format="auto" (default) to determine which format to use.
RESPONSE_MAPPING = {
    "json": "json",
    "text": "text",
    "html": "html",
    "JSONResponse": "json",
    "text/plain": "text",
    "text/html": "html",
    "application/json": "json",
}


def check_error_format(format):
    """Check that the format is known."""
    if format not in MIME_BY_CONFIG and format != "auto":
        raise SanicException(f"Unknown format: {format}")


def exception_response(
    request: Request,
    exception: Exception,
    debug: bool,
    fallback: str,
    base: t.Type[BaseRenderer],
    renderer: t.Optional[t.Type[BaseRenderer]] = None,
) -> HTTPResponse:
    """Render a response for the default FALLBACK exception handler."""
    if not renderer:
        mt = guess_mime(request, fallback)
        renderer = RENDERERS_BY_CONTENT_TYPE.get(mt, base)

    renderer = t.cast(t.Type[BaseRenderer], renderer)
    return renderer(request, exception, debug).render()


def guess_mime(req: Request, fallback: str) -> str:
    """Guess the MIME type for the response based upon the request."""
    # Attempt to find a suitable MIME format for the response.
    # Insertion-ordered map of formats["html"] = "source of that suggestion"
    formats = {}
    name = ""
    # Route error_format (by magic from handler code if auto, the default)
    if req.route:
        name = req.route.name
        f = req.route.extra.error_format
        if f in MIME_BY_CONFIG:
            formats[f] = name

    if not formats and fallback in MIME_BY_CONFIG:
        formats[fallback] = "FALLBACK_ERROR_FORMAT"

    # If still not known, check for the request for clues of JSON
    if not formats and fallback == "auto" and req.accept.match(JSON):
        if JSON in req.accept:  # Literally, not wildcard
            formats["json"] = "request.accept"
        elif JSON in req.headers.getone("content-type", ""):
            formats["json"] = "content-type"
        # DEPRECATION: Remove this block in 24.3
        else:
            c = None
            try:
                c = req.json
            except BadRequest:
                pass
            if c:
                formats["json"] = "request.json"
                deprecation(
                    "Response type was determined by the JSON content of "
                    "the request. This behavior is deprecated and will be "
                    "removed in v24.3. Please specify the format either by\n"
                    f'  error_format="json" on route {name}, by\n'
                    '  FALLBACK_ERROR_FORMAT = "json", or by adding header\n'
                    "  accept: application/json to your requests.",
                    24.3,
                )

    # Any other supported formats
    if fallback == "auto":
        for k in MIME_BY_CONFIG:
            if k not in formats:
                formats[k] = "any"

    mimes = [MIME_BY_CONFIG[k] for k in formats]
    m = req.accept.match(*mimes)
    if m:
        format = CONFIG_BY_MIME[m.mime]
        source = formats[format]
        logger.debug(
            "Error Page: The client accepts %s, using '%s' from %s",
            m.header,
            format,
            source,
        )
    else:
        logger.debug(
            "Error Page: No format found, the client accepts %s",
            repr(req.accept),
        )
    return m.mime
