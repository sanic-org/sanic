from typing import Any, Mapping

import tracerite.html

from html5tagger import E
from tracerite import html_traceback, inspector

from sanic.request import Request

from .base import BasePage


# Avoid showing the request in the traceback variable inspectors
inspector.blacklist_types += (Request,)

ENDUSER_TEXT = """We're sorry, but it looks like something went wrong. Please try refreshing the page or navigating back to the homepage. If the issue persists, our technical team is working to resolve it as soon as possible. We apologize for the inconvenience and appreciate your patience."""  # noqa: E501


class ErrorPage(BasePage):
    STYLE_APPEND = tracerite.html.style

    def __init__(
        self,
        title: str,
        text: str,
        request: Request,
        exc: Exception,
        full: bool,
    ) -> None:
        super().__init__()
        # Internal server errors come with the text of the exception,
        # which we don't want to show to the user.
        # FIXME: Needs to be done in a better way, elsewhere
        if "Internal Server Error" in title:
            text = "The application encountered an unexpected error and could not continue."  # noqa: E501
        name = request.app.name.replace("_", " ").strip()
        if name.islower():
            name = name.title()
        self.TITLE = E("Application ").strong(name)(
            " cannot handle your request"
        )
        self.title = title
        self.text = text
        self.request = request
        self.exc = exc
        self.full = full

    def _head(self) -> None:
        self.doc._script(tracerite.html.javascript)
        super()._head()

    def _body(self) -> None:
        debug = self.request.app.debug
        try:
            route_name = self.request.route.name
        except AttributeError:
            route_name = "[route not found]"
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
            with self.doc.details(open=self.full, class_="smalltext"):
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
                    self.doc.h2(f"Exception in {route_name}:")
                    self.doc(html_traceback(self.exc, include_js_css=False))

                self._key_value_table(
                    f"{self.request.method} {self.request.path}",
                    "request-headers",
                    self.request.headers,
                )

    def _key_value_table(
        self, title: str, table_id: str, data: Mapping[str, Any]
    ) -> None:
        self.doc.h2(title)
        with self.doc.dl(id=table_id, class_="key-value-table smalltext"):
            for key, value in data.items():
                # Reading values may cause a new exception, so suppress it
                try:
                    value = str(value)
                except Exception:
                    value = E.em("Unable to display value")
                self.doc.dt.span(key, class_="nobr key").span(": ").dd(value)
