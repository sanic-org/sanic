from .base import BasePage
from sanic.request import Request
from contextlib import suppress
from html5tagger import E
from tracerite import html_traceback, inspector
import tracerite.html

# Avoid showing the request in the traceback variable inspectors
inspector.blacklist_types += Request,

class ErrorPage(BasePage):
    STYLE_APPEND = tracerite.html.style
    def __init__(self, title: str, text: str, request: Request, exc: Exception, full: bool) -> None:
        super().__init__()
        # Internal server errors come with the text of the exception, which we don't want to show to the user.
        # FIXME: This needs to be done some place else but I am not digging into that now.
        if "Internal Server Error" in title:
            text = "The application encountered an unexpected error and could not continue."
        self.TITLE = E(f"App {request.app.name} cannot handle your request")
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
            context = getattr(self.exc, "context", None) or {}
            if debug:
                context.update(getattr(self.exc, "extra", None) or {})
            # Show context and extra details if available on the exception
            if context:
                # Printing values may easily cause a new exception, so suppress it
                with self.doc.table(id="exception-context"), suppress(Exception):
                    for k, v in context.items():
                        self.doc.tr.td(k).td(v)
            if not debug:
                return
            # Show additional details in debug mode, open by default for 500 errors
            with self.doc.details(open=self.full, class_="smalltext"):
                self.doc.summary("Details for developers (Sanic debug mode only)")
                if self.exc:
                    self.doc.h2(f"Exception in {route_name}:")
                    # skip_outmost=1 to hide Sanic.handle_request
                    self.doc(html_traceback(self.exc, skip_outmost=1, include_js_css=False))

                self.doc.h2(f"{self.request.method} {self.request.path}")
                with self.doc.table(id="request-headers"):
                    for k, v in self.request.headers.items():
                        self.doc.tr.td(f"{k}:", class_="nobr").td(v)
