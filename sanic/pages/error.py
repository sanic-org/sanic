from collections.abc import Mapping
from typing import Any

import tracerite.html

from html5tagger import E
from tracerite import html_traceback, inspector

from sanic.request import Request

from .base import BasePage


# Avoid showing the request in the traceback variable inspectors
inspector.blacklist_types += (Request,)

ENDUSER_TEXT = """\
We're sorry, but it looks like something went wrong. Please try refreshing \
the page or navigating back to the homepage. If the issue persists, our \
technical team is working to resolve it as soon as possible. We apologize \
for the inconvenience and appreciate your patience.\
"""


class ErrorPage(BasePage):
    """Page for displaying an error."""

    STYLE_APPEND = tracerite.html.style

    def __init__(
        self,
        debug: bool,
        title: str,
        text: str,
        request: Request,
        exc: Exception,
    ) -> None:
        super().__init__(debug)
        name = request.app.name.replace("_", " ").strip()
        if name.islower():
            name = name.title()
        self.TITLE = f"Application {name} cannot handle your request"
        self.HEADING = E("Application ").strong(name)(
            " cannot handle your request"
        )
        self.title = title
        self.text = text
        self.request = request
        self.exc = exc
        self.details_open = not getattr(exc, "quiet", False)

    def _head(self) -> None:
        self.doc._script(tracerite.html.javascript)
        super()._head()

    def _body(self) -> None:
        debug = self.request.app.debug
        route_name = self.request.name or "[route not found]"
        with self.doc.main:
            self.doc.h1(f"⚠️ {self.title}").p(self.text)
            # Show context details if available on the exception
            context = getattr(self.exc, "context", None)
            if context:
                self._key_value_table(
                    "Issue context", "exception-context", context
                )

            if not debug:
                with self.doc.div(id="enduser"):
                    self.doc.p(ENDUSER_TEXT).p.a("Front Page", href="/")
                return
            # Show additional details in debug mode,
            # open by default for 500 errors
            with self.doc.details(open=self.details_open, class_="smalltext"):
                # Show extra details if available on the exception
                extra = getattr(self.exc, "extra", None)
                if extra:
                    self._key_value_table(
                        "Issue extra data", "exception-extra", extra
                    )

                self.doc.summary(
                    "Details for developers (Sanic debug mode only)"
                )
                if self.exc:
                    with self.doc.div(class_="exception-wrapper"):
                        self.doc.h2(f"Exception in {route_name}:")
                        self.doc(
                            html_traceback(self.exc, include_js_css=False)
                        )

                self._key_value_table(
                    f"{self.request.method} {self.request.path}",
                    "request-headers",
                    self.request.headers,
                )

    def _key_value_table(
        self, title: str, table_id: str, data: Mapping[str, Any]
    ) -> None:
        with self.doc.div(class_="key-value-display"):
            self.doc.h2(title)
            with self.doc.dl(id=table_id, class_="key-value-table smalltext"):
                for key, value in data.items():
                    # Reading values may cause a new exception, so suppress it
                    try:
                        value = str(value)
                    except Exception:
                        value = E.em("Unable to display value")
                    self.doc.dt.span(key, class_="nobr key").span(": ").dd(
                        value
                    )
