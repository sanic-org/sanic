from typing import Any, Mapping

import tracerite.html

from html5tagger import E
from tracerite import html_traceback, inspector

from sanic.request import Request

from .base import BasePage


# Avoid showing the request in the traceback variable inspectors
inspector.blacklist_types += (Request,)


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
        # Internal server errors come with the text of the exception, which we don't want to show to the user.
        # FIXME: This needs to be done some place else but I am not digging into that now.
        if "Internal Server Error" in title:
            text = "The application encountered an unexpected error and could not continue."
        self.TITLE = E.strong(request.app.name)(" cannot handle your request")
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
                return
            # Show additional details in debug mode,
            # open by default for 500 errors
            with self.doc.details(open=self.full, class_="smalltext"):
                # Show extra details if available on the exception
                extra = getattr(self.exc, "extra", None)
                if extra:
                    self._key_value_table(
                        "Exception extra data", "exception-extra", extra
                    )

                self.doc.summary(
                    "Details for developers (Sanic debug mode only)"
                )
                if self.exc:
                    self.doc.h2(f"Exception in {route_name}:")
                    # skip_outmost=1 to hide Sanic.handle_request
                    self.doc(
                        html_traceback(
                            self.exc, skip_outmost=1, include_js_css=False
                        )
                    )

                self._key_value_table(
                    f"{self.request.method} {self.request.path}",
                    "request-headers",
                    self.request.headers,
                )

    def _key_value_table(
        self, title: str, table_id: str, data: Mapping[str, Any]
    ) -> None:
        with self.doc.table(id=table_id, class_="key-value-table smalltext"):
            self.doc.caption(title)
            for key, value in data.items():
                try:
                    self.doc.tr.td(key, class_="nobr key").td(value)
                # Printing values may cause a new exception, so suppress it
                except Exception:
                    self.doc.tr.td(key, class_="nobr key").td.em(
                        "Unable to display value"
                    )
