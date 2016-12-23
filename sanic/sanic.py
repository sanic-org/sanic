from asyncio import get_event_loop
from collections import deque
from functools import partial
from inspect import isawaitable, stack, getmodulename
from multiprocessing import Process, Event
from signal import signal, SIGTERM, SIGINT
from time import sleep
from traceback import format_exc

from .config import Config
from .exceptions import Handler
from .log import log, logging
from .response import HTTPResponse
from .router import Router
from .server import serve
from .static import register as static_register
from .exceptions import ServerError


class Sanic:
    def __init__(self, name=None, router=None, error_handler=None):
        if name is None:
            frame_records = stack()[1]
            name = getmodulename(frame_records[1])
        self.name = name
        self.router = router or Router()
        self.error_handler = error_handler or Handler(self)
        self.config = Config()
        self.request_middleware = deque()
        self.response_middleware = deque()
        self.blueprints = {}
        self._blueprint_order = []
        self.loop = None
        self.debug = None

        # Register alternative method names
        self.go_fast = self.run

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

        # Fix case where the user did not prefix the URL with a /
        # and will probably get confused as to why it's not working
        if not uri.startswith('/'):
            uri = '/' + uri

        def response(handler):
            self.router.add(uri=uri, methods=methods, handler=handler)
            return handler

        return response

    def add_route(self, handler, uri, methods=None):
        """
        A helper method to register class instance or
        functions as a handler to the application url
        routes.
        :param handler: function or class instance
        :param uri: path of the URL
        :param methods: list or tuple of methods allowed
        :return: function or class instance
        """
        self.route(uri=uri, methods=methods)(handler)
        return handler

    # Decorator
    def exception(self, *exceptions):
        """
        Decorates a function to be registered as a handler for exceptions
        :param *exceptions: exceptions
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
               use_modified_since=True):
        """
        Registers a root to serve files from.  The input can either be a file
        or a directory.  See
        """
        static_register(self, uri, file_or_directory, pattern,
                        use_modified_since)

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
        log.warning("Use of register_blueprint will be deprecated in "
                    "version 1.0.  Please use the blueprint method instead")
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
                        "An error occured while handling an error")

        response_callback(response)

    # -------------------------------------------------------------------- #
    # Execution
    # -------------------------------------------------------------------- #

    def run(self, host="127.0.0.1", port=8000, debug=False, before_start=None,
            after_start=None, before_stop=None, after_stop=None, sock=None,
            workers=1, loop=None):
        """
        Runs the HTTP Server and listens until keyboard interrupt or term
        signal. On termination, drains connections before closing.
        :param host: Address to host on
        :param port: Port to host on
        :param debug: Enables debug output (slows server)
        :param before_start: Function to be executed before the server starts
        accepting connections
        :param after_start: Function to be executed after the server starts
        accepting connections
        :param before_stop: Function to be executed when a stop signal is
        received before it is respected
        :param after_stop: Function to be executed when all requests are
        complete
        :param sock: Socket for the server to accept connections from
        :param workers: Number of processes
        received before it is respected
        :param loop: asyncio compatible event loop
        :return: Nothing
        """
        self.error_handler.debug = True
        self.debug = debug
        self.loop = loop

        server_settings = {
            'host': host,
            'port': port,
            'sock': sock,
            'debug': debug,
            'request_handler': self.handle_request,
            'error_handler': self.error_handler,
            'request_timeout': self.config.REQUEST_TIMEOUT,
            'request_max_size': self.config.REQUEST_MAX_SIZE,
            'loop': loop
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
                if type(args) is not list:
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

        # Serve
        log.info('Goin\' Fast @ http://{}:{}'.format(host, port))

        try:
            if workers == 1:
                serve(**server_settings)
            else:
                log.info('Spinning up {} workers...'.format(workers))

                self.serve_multiple(server_settings, workers)

        except Exception as e:
            log.exception(
                'Experienced exception while trying to serve')

        log.info("Server Stopped")

    def stop(self):
        """
        This kills the Sanic
        """
        get_event_loop().stop()

    @staticmethod
    def serve_multiple(server_settings, workers, stop_event=None):
        """
        Starts multiple server processes simultaneously.  Stops on interrupt
        and terminate signals, and drains connections when complete.
        :param server_settings: kw arguments to be passed to the serve function
        :param workers: number of workers to launch
        :param stop_event: if provided, is used as a stop signal
        :return:
        """
        server_settings['reuse_port'] = True

        # Create a stop event to be triggered by a signal
        if not stop_event:
            stop_event = Event()
        signal(SIGINT, lambda s, f: stop_event.set())
        signal(SIGTERM, lambda s, f: stop_event.set())

        processes = []
        for _ in range(workers):
            process = Process(target=serve, kwargs=server_settings)
            process.start()
            processes.append(process)

        # Infinitely wait for the stop event
        try:
            while not stop_event.is_set():
                sleep(0.3)
        except:
            pass

        log.info('Spinning down workers...')
        for process in processes:
            process.terminate()
        for process in processes:
            process.join()
