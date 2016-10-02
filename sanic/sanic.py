import inspect
from .router import Router
from .response import HTTPResponse, error_404
from .server import serve
from .log import log

class Sanic:
    name = None
    routes = []

    def __init__(self, name, router=None):
        self.name = name
        self.router = router or Router(default=error_404)

    def route(self, *args, **kwargs):
        def response(handler):
            handler.is_async = inspect.iscoroutinefunction(handler)
            self.router.add(*args, **kwargs, handler=handler)
            return handler

        return response

    def run(self, host="127.0.0.1", port=8000, debug=False):
        return serve(router=self.router, host=host, port=port, debug=debug)