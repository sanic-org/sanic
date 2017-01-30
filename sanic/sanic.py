import logging
from asyncio import get_event_loop
from collections import deque
from functools import partial
from inspect import isawaitable, stack, getmodulename
from traceback import format_exc
import warnings

from .config import Config
from .handlers import ErrorHandler
from .constants import HTTP_METHODS
from .exceptions import ServerError
from .handlers import ErrorHandler
from .log import log
from .response import HTTPResponse
from .router import Router
from .server import serve, serve_multiple, HttpProtocol
from .static import register as static_register


class Sanic:
    def __init__(self, name=None, router=None,
                 error_handler=None):
        # Only set up a default log handler if the
        # end-user application didn't set anything up.
        if not logging.root.handlers and log.level == logging.NOTSET:
            formatter = logging.Formatter(
                "%(asctime)s: %(levelname)s: %(message)s")
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            log.addHandler(handler)
            log.setLevel(logging.INFO)
        if name is None:
            frame_records = stack()[1]
            name = getmodulename(frame_records[1])
        self.name = name
        self.router = router or Router()
        self.error_handler = error_handler or ErrorHandler()
        self.config = Config()
        self.request_middleware = deque()
        self.response_middleware = deque()
        self.blueprints = {}
        self._blueprint_order = []
        self.debug = None
        self.sock = None
        self.processes = None

        # Register alternative method names
        self.go_fast = self.run

    # -------------------------------------------------------------------- #
    # Registration
    # -------------------------------------------------------------------- #

    # Decorator
    def route(self, uri, methods=frozenset({'GET'}), host=None):
        """
        Decorates a function to be registered as a route

        :param uri: path of the URL
        :param methods: list or tuple of methods allowed
        :return: decorated function
        """

        # Fix case where the user did not prefix the URL with a /
        # and will probably get confused as to why it's not working
        if not uri.startswith('/'):
            uri = '/' + uri

        def response(handler):
            self.router.add(uri=uri, methods=methods, handler=handler,
                            host=host)
            return handler

        return response

    # Shorthand method decorators
    def get(self, uri, host=None):
        return self.route(uri, methods=frozenset({"GET"}), host=host)

    def post(self, uri, host=None):
        return self.route(uri, methods=frozenset({"POST"}), host=host)

    def put(self, uri, host=None):
        return self.route(uri, methods=frozenset({"PUT"}), host=host)

    def head(self, uri, host=None):
        return self.route(uri, methods=frozenset({"HEAD"}), host=host)

    def options(self, uri, host=None):
        return self.route(uri, methods=frozenset({"OPTIONS"}), host=host)

    def patch(self, uri, host=None):
        return self.route(uri, methods=frozenset({"PATCH"}), host=host)

    def delete(self, uri, host=None):
        return self.route(uri, methods=["DELETE"], host=host)

    def add_route(self, handler, uri, methods=frozenset({'GET'}), host=None):
        """
        A helper method to register class instance or
        functions as a handler to the application url
        routes.

        :param handler: function or class instance
        :param uri: path of the URL
        :param methods: list or tuple of methods allowed, these are overridden
                        if using a HTTPMethodView
        :return: function or class instance
        """
        # Handle HTTPMethodView differently
        if hasattr(handler, 'view_class'):
            methods = frozenset(HTTP_METHODS)
        self.route(uri=uri, methods=methods, host=host)(handler)
        return handler

    def remove_route(self, uri, clean_cache=True, host=None):
        self.router.remove(uri, clean_cache, host)

    # Decorator
    def exception(self, *exceptions):
        """
        Decorates a function to be registered as a handler for exceptions

        :param exceptions: exceptions
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
        attach_to = 'request'

        def register_middleware(middleware):
            if attach_to == 'request':
                self.request_middleware.append(middleware)
            if attach_to == 'response':
                self.response_middleware.appendleft(middleware)
            return middleware

        # Detect which way this was called, @middleware or @middleware('AT')
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            return register_middleware(args[0])
        else:
            attach_to = args[0]
            return register_middleware

    # Static Files
    def static(self, uri, file_or_directory, pattern='.+',
               use_modified_since=True, use_content_range=False):
        """
        Registers a root to serve files from.  The input can either be a file
        or a directory.  See
        """
        static_register(self, uri, file_or_directory, pattern,
                        use_modified_since, use_content_range)

    def blueprint(self, blueprint, **options):
        """
        Registers a blueprint on the application.

        :param blueprint: Blueprint object
        :param options: option dictionary with blueprint defaults
        :return: Nothing
        """
        if blueprint.name in self.blueprints:
            assert self.blueprints[blueprint.name] is blueprint, \
                'A blueprint with the name "%s" is already registered.  ' \
                'Blueprint names must be unique.' % \
                (blueprint.name,)
        else:
            self.blueprints[blueprint.name] = blueprint
            self._blueprint_order.append(blueprint)
        blueprint.register(self, options)

    def register_blueprint(self, *args, **kwargs):
        # TODO: deprecate 1.0
        if self.debug:
            warnings.simplefilter('default')
        warnings.warn("Use of register_blueprint will be deprecated in "
                      "version 1.0.  Please use the blueprint method"
                      " instead",
                      DeprecationWarning)
        return self.blueprint(*args, **kwargs)

    # -------------------------------------------------------------------- #
    # Request Handling
    # -------------------------------------------------------------------- #

    def converted_response_type(self, response):
        pass

    async def handle_request(self, request, response_callback):
        """
        Takes a request from the HTTP Server and returns a response object to
        be sent back The HTTP Server only expects a response object, so
        exception handling must be done here

        :param request: HTTP Request object
        :param response_callback: Response function to be called with the
                                  response as the only argument
        :return: Nothing
        """
        try:
            # -------------------------------------------- #
            # Request Middleware
            # -------------------------------------------- #

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
                # -------------------------------------------- #
                # Execute Handler
                # -------------------------------------------- #

                # Fetch handler from router
                handler, args, kwargs = self.router.get(request)
                if handler is None:
                    raise ServerError(
                        ("'None' was returned while requesting a "
                         "handler from the router"))

                # Run response handler
                response = handler(request, *args, **kwargs)
                if isawaitable(response):
                    response = await response

            # -------------------------------------------- #
            # Response Middleware
            # -------------------------------------------- #

            if self.response_middleware:
                for middleware in self.response_middleware:
                    _response = middleware(request, response)
                    if isawaitable(_response):
                        _response = await _response
                    if _response:
                        response = _response
                        break

        except Exception as e:
            # -------------------------------------------- #
            # Response Generation Failed
            # -------------------------------------------- #

            try:
                response = self.error_handler.response(request, e)
                if isawaitable(response):
                    response = await response
            except Exception as e:
                if self.debug:
                    response = HTTPResponse(
                        "Error while handling error: {}\nStack: {}".format(
                            e, format_exc()))
                else:
                    response = HTTPResponse(
                        "An error occurred while handling an error")

        response_callback(response)

    # -------------------------------------------------------------------- #
    # Execution
    # -------------------------------------------------------------------- #

    def run(self, host="127.0.0.1", port=8000, debug=False, before_start=None,
            after_start=None, before_stop=None, after_stop=None, ssl=None,
            sock=None, workers=1, loop=None, protocol=HttpProtocol,
            backlog=100, stop_event=None, register_sys_signals=True):
        """
        Runs the HTTP Server and listens until keyboard interrupt or term
        signal. On termination, drains connections before closing.

        :param host: Address to host on
        :param port: Port to host on
        :param debug: Enables debug output (slows server)
        :param before_start: Functions to be executed before the server starts
                             accepting connections
        :param after_start: Functions to be executed after the server starts
                            accepting connections
        :param before_stop: Functions to be executed when a stop signal is
                            received before it is respected
        :param after_stop: Functions to be executed when all requests are
                           complete
        :param ssl: SSLContext for SSL encryption of worker(s)
        :param sock: Socket for the server to accept connections from
        :param workers: Number of processes
                        received before it is respected
        :param protocol: Subclass of asyncio protocol class
        :return: Nothing
        """
        server_settings = self._helper(
            host=host, port=port, debug=debug, before_start=before_start,
            after_start=after_start, before_stop=before_stop,
            after_stop=after_stop, ssl=ssl, sock=sock, workers=workers,
            loop=loop, protocol=protocol, backlog=backlog,
            stop_event=stop_event, register_sys_signals=register_sys_signals)
        try:
            if workers == 1:
                serve(**server_settings)
            else:
                serve_multiple(server_settings, workers, stop_event)

        except Exception as e:
            log.exception(
                'Experienced exception while trying to serve')

        log.info("Server Stopped")

    def stop(self):
        """This kills the Sanic"""
        get_event_loop().stop()

    async def create_server(self, host="127.0.0.1", port=8000, debug=False,
                            before_start=None, after_start=None,
                            before_stop=None, after_stop=None, ssl=None,
                            sock=None, loop=None, protocol=HttpProtocol,
                            backlog=100, stop_event=None):
        """
        Asynchronous version of `run`.
        """
        server_settings = self._helper(
            host=host, port=port, debug=debug, before_start=before_start,
            after_start=after_start, before_stop=before_stop,
            after_stop=after_stop, ssl=ssl, sock=sock, loop=loop,
            protocol=protocol, backlog=backlog, stop_event=stop_event,
            run_async=True)

        # Serve
        proto = "http"
        if ssl is not None:
            proto = "https"
        log.info('Goin\' Fast @ {}://{}:{}'.format(proto, host, port))

        return await serve(**server_settings)

    def _helper(self, host="127.0.0.1", port=8000, debug=False,
                before_start=None, after_start=None, before_stop=None,
                after_stop=None, ssl=None, sock=None, workers=1, loop=None,
                protocol=HttpProtocol, backlog=100, stop_event=None,
                register_sys_signals=True, run_async=False):
        """
        Helper function used by `run` and `create_server`.
        """

        self.error_handler.debug = debug
        self.debug = debug
        self.loop = loop = get_event_loop()

        if loop is not None:
            if self.debug:
                warnings.simplefilter('default')
            warnings.warn("Passing a loop will be deprecated in version"
                          " 0.4.0 https://github.com/channelcat/sanic/"
                          "pull/335 has more information.",
                          DeprecationWarning)

        server_settings = {
            'protocol': protocol,
            'host': host,
            'port': port,
            'sock': sock,
            'ssl': ssl,
            'debug': debug,
            'request_handler': self.handle_request,
            'error_handler': self.error_handler,
            'request_timeout': self.config.REQUEST_TIMEOUT,
            'request_max_size': self.config.REQUEST_MAX_SIZE,
            'loop': loop,
            'register_sys_signals': register_sys_signals,
            'backlog': backlog
        }

        # -------------------------------------------- #
        # Register start/stop events
        # -------------------------------------------- #

        for event_name, settings_name, args, reverse in (
                ("before_server_start", "before_start", before_start, False),
                ("after_server_start", "after_start", after_start, False),
                ("before_server_stop", "before_stop", before_stop, True),
                ("after_server_stop", "after_stop", after_stop, True),
                ):
            listeners = []
            for blueprint in self.blueprints.values():
                listeners += blueprint.listeners[event_name]
            if args:
                if callable(args):
                    args = [args]
                listeners += args
            if reverse:
                listeners.reverse()
            # Prepend sanic to the arguments when listeners are triggered
            listeners = [partial(listener, self) for listener in listeners]
            server_settings[settings_name] = listeners

        if debug:
            log.setLevel(logging.DEBUG)
        log.debug(self.config.LOGO)

        if run_async:
            server_settings['run_async'] = True

        # Serve
        proto = "http"
        if ssl is not None:
            proto = "https"
        log.info('Goin\' Fast @ {}://{}:{}'.format(proto, host, port))

        return server_settings
