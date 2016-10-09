from .config import Config
from .exceptions import Handler
from .log import log
from .response import HTTPResponse
from .router import Router
from .server import serve

class Sanic:
    name = None
    debug = None
    router = None
    error_handler = None
    routes = []

    def __init__(self, name, router=None, error_handler=None):
        self.name = name
        self.router = router or Router()
        self.error_handler = error_handler or Handler()
        self.config = Config()

    def route(self, uri):
        def response(handler):
            self.router.add(uri=uri, handler=handler)
            return handler

        return response

    def handler(self, *args, **kwargs):
        def response(handler):
            self.error_handler.add(*args, **kwargs)
            return handler

        return response

    def run(self, host="127.0.0.1", port=8000, debug=False, on_start=None, on_stop=None):
        self.error_handler.debug=True
        self.debug = debug
        return serve(sanic=self, host=host, port=port, debug=debug, on_start=on_start, on_stop=on_stop)