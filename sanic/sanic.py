from .config import Config
from .exceptions import Handler
from .log import log, logging
from .response import HTTPResponse
from .router import Router
from .server import serve
from .exceptions import ServerError
from inspect import isawaitable
from traceback import format_exc

class Sanic:
    name = None
    debug = None
    router = None
    error_handler = None
    routes = []

    def __init__(self, name, router=None, error_handler=None):
        self.name = name
        self.router = router or Router()
        self.error_handler = error_handler or Handler(self)
        self.config = Config()

    # -------------------------------------------------------------------- #
    # Decorators
    # -------------------------------------------------------------------- #

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
            handler, args, kwargs = self.router.get(request)
            if handler is None:
                raise ServerError("'None' was returned while requesting a handler from the router")

            response = handler(request, *args, **kwargs)
            if isawaitable(response):
                response = await response

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

    def run(self, host="127.0.0.1", port=8000, debug=False, before_start=None, before_stop=None):
        """
        Runs the HTTP Server and listens until keyboard interrupt or term signal.
        On termination, drains connections before closing.
        :param host: Address to host on
        :param port: Port to host on
        :param debug: Enables debug output (slows server)
        :param before_start: Function to be executed after the event loop is created and before the server starts
        :param before_stop: Function to be executed when a stop signal is received before it is respected
        :return: Nothing
        """
        self.error_handler.debug=True
        self.debug = debug

        if debug:
            log.setLevel(logging.DEBUG)
        log.debug(self.config.LOGO)

        # Serve
        log.info('Goin\' Fast @ {}:{}'.format(host, port))

        try:
            serve(
                host=host,
                port=port,
                debug=debug,
                before_start=before_start,
                before_stop=before_stop,
                request_handler=self.handle_request,
                request_timeout=self.config.REQUEST_TIMEOUT,
                request_max_size=self.config.REQUEST_MAX_SIZE,
            )
        except:
            pass