from .base import BasePage
from sanic.request import Request

from html5tagger import E
from niceback import html_traceback, inspector

# Avoid showing the request in the traceback variable inspectors
inspector.blacklist_types += Request,

class ErrorPage(BasePage):
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

    def _body(self) -> None:
        with self.doc.main:
            self.doc.h1(f"⚠️ {self.title}").p(self.text)
            if not self.request.app.debug:
                return
            # Show additional details in debug mode, open by default for 500 errors
            with self.doc.details(open=self.full, class_="smalltext"):
                self.doc.summary("Details for developers (Sanic debug mode only)")
                if self.exc:
                    self.doc.h2(f"Exception in {self.request.route.name}:")
                    # skip_outmost=1 to hide Sanic.handle_request
                    self.doc(html_traceback(self.exc, skip_outmost=1))

                self.doc.h2(f"{self.request.method} {self.request.path}")
                with self.doc.table(id="request-headers"):
                    for k, v in self.request.headers.items():
                        self.doc.tr.td(f"{k}:", class_="nobr").td(v)
