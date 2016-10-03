from .router import Router
from .exceptions import Handler
from .response import HTTPResponse
from .server import serve
from .log import log

class Sanic:
    name = None
    router = None
    error_handler = None
    routes = []

    def __init__(self, name, router=None, error_handler=None):
        self.name = name
        self.router = router or Router()
        self.error_handler = error_handler or Handler()

    def route(self, *args, **kwargs):
        def response(handler):
            self.add_route(handler, *args, **kwargs)
            return handler

        return response

    def add_route(self, handler, *args, **kwargs):
        self.router.add(*args, **kwargs, handler=handler)

    def run(self, host="127.0.0.1", port=8000, debug=False):
        return serve(sanic=self, host=host, port=port, debug=debug)