import asyncio
from inspect import isawaitable
from traceback import format_exc
from types import FunctionType

from .config import Config
from .exceptions import Handler
from .log import log, logging
from .middleware import Middleware
from .response import HTTPResponse
from .router import Router
from .server import serve
from .exceptions import ServerError


class Sanic:
    def __init__(self, name, router=None, error_handler=None):
        self.name = name
        self.router = router or Router()
        self.router = router or Router()
        self.error_handler = error_handler or Handler(self)
        self.config = Config()
        self.request_middleware = []
        self.response_middleware = []

    # -------------------------------------------------------------------- #
    # Registration
    # -------------------------------------------------------------------- #

    # Decorator
    def route(self, uri, methods=None):
        """
        Decorates a function to be registered as a route
        :param uri: path of the URL
        :param methods: list or tuple of methods allowed
        :return: decorated function
        """

        def response(handler):
            self.router.add(uri=uri, methods=methods, handler=handler)
            return handler

        return response

    # Decorator
    def exception(self, *exceptions):
        """
        Decorates a function to be registered as a route
        :param uri: path of the URL
        :param methods: list or tuple of methods allowed
        :return: decorated function
        """

        def response(handler):
            for exception in exceptions:
                self.error_handler.add(exception, handler)
            return handler

        return response

    # Decorator
    def middleware(self, *args, **kwargs):
        """
        Decorates and registers middleware to be called before a request
        can either be called as @app.middleware or @app.middleware('request')
        """
        middleware = None
        attach_to = 'request'

        def register_middleware(middleware):
            if attach_to == 'request':
                self.request_middleware.append(middleware)
            if attach_to == 'response':
                self.response_middleware.append(middleware)
            return middleware

        # Detect which way this was called, @middleware or @middleware('AT')
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            return register_middleware(args[0])
        else:
            attach_to = args[0]
            return register_middleware

        if isinstance(middleware, FunctionType):
            middleware = Middleware(process_request=middleware)

        return middleware

    # -------------------------------------------------------------------- #
    # Request Handling
    # -------------------------------------------------------------------- #

    async def handle_request(self, request, response_callback):
        """
        Takes a request from the HTTP Server and returns a response object to be sent back
        The HTTP Server only expects a response object, so exception handling must be done here
        :param request: HTTP Request object
        :param response_callback: Response function to be called with the response as the only argument
        :return: Nothing
        """
        try:
            # Middleware process_request
            response = False
            # The if improves speed.  I don't know why
            if self.request_middleware:
                for middleware in self.request_middleware:
                    response = middleware(request)
                    if isawaitable(response):
                        response = await response
                    if response:
                        break

            # No middleware results
            if not response:
                # Fetch handler from router
                handler, args, kwargs = self.router.get(request)
                if handler is None:
                    raise ServerError("'None' was returned while requesting a handler from the router")

                # Run response handler
                response = handler(request, *args, **kwargs)
                if isawaitable(response):
                    response = await response

                # Middleware process_response
                if self.response_middleware:
                    for middleware in self.response_middleware:
                        _response = middleware(request, response)
                        if isawaitable(_response):
                            _response = await _response
                        if _response:
                            response = _response
                            break

        except Exception as e:
            try:
                response = self.error_handler.response(request, e)
                if isawaitable(response):
                    response = await response
            except Exception as e:
                if self.debug:
                    response = HTTPResponse("Error while handling error: {}\nStack: {}".format(e, format_exc()))
                else:
                    response = HTTPResponse("An error occured while handling an error")

        response_callback(response)

    # -------------------------------------------------------------------- #
    # Execution
    # -------------------------------------------------------------------- #

    def run(self, host="127.0.0.1", port=8000, debug=False, after_start=None, before_stop=None):
        """
        Runs the HTTP Server and listens until keyboard interrupt or term signal.
        On termination, drains connections before closing.
        :param host: Address to host on
        :param port: Port to host on
        :param debug: Enables debug output (slows server)
        :param after_start: Function to be executed after the server starts listening
        :param before_stop: Function to be executed when a stop signal is received before it is respected
        :return: Nothing
        """
        self.error_handler.debug = True
        self.debug = debug

        if debug:
            log.setLevel(logging.DEBUG)
        log.debug(self.config.LOGO)

        # Serve
        log.info('Goin\' Fast @ http://{}:{}'.format(host, port))

        try:
            serve(
                host=host,
                port=port,
                debug=debug,
                after_start=after_start,
                before_stop=before_stop,
                request_handler=self.handle_request,
                request_timeout=self.config.REQUEST_TIMEOUT,
                request_max_size=self.config.REQUEST_MAX_SIZE,
            )
        except:
            pass

    def stop(self):
        """
        This kills the Sanic
        """
        asyncio.get_event_loop().stop()
