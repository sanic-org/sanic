from .config import Config
from .exceptions import Handler
from .log import log, logging
from .response import HTTPResponse
from .router import Router
from .server import serve
from .exceptions import ServerError
from inspect import isawaitable

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

    def exception(self, *args, **kwargs):
        def response(handler):
            self.error_handler.add(*args, **kwargs)
            return handler

        return response

    async def handle_request(self, request, respond):
        try:
            handler = self.router.get(request)
            if handler is None:
                raise ServerError("'None' was returned while requesting a handler from the router")

            response = handler(request)
            # Check if the handler is asynchronous
            if isawaitable(response):
                response = await response

        except Exception as e:
            try:
                response = self.error_handler.response(request, e)
            except Exception as e:
                if self.debug:
                    response = HTTPResponse("Error while handling error: {}\nStack: {}".format(e, format_exc()))
                else:
                    response = HTTPResponse("An error occured while handling an error")

        respond(response)


    def run(self, host="127.0.0.1", port=8000, debug=False, on_start=None, on_stop=None):
        self.error_handler.debug=True
        self.debug = debug

        if debug:
            log.setLevel(logging.DEBUG)
        log.debug(self.config.LOGO)

        # Serve
        log.info('Goin\' Fast @ {}:{}'.format(host, port))

        return serve(
            host=host,
            port=port,
            debug=debug,
            on_start=on_start,
            on_stop=on_stop,
            request_handler=self.handle_request,
            request_timeout=self.config.REQUEST_TIMEOUT,
            request_max_size=self.config.REQUEST_MAX_SIZE,
        )