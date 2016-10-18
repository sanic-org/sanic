from asyncio import get_event_loop
from inspect import isawaitable
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
from .exceptions import ServerError


class Sanic:
    def __init__(self, name, router=None, error_handler=None):
        self.name = name
        self.router = router or Router()
        self.error_handler = error_handler or Handler(self)
        self.config = Config()
        self.request_middleware = []
        self.response_middleware = []
        self.blueprints = {}
        self._blueprint_order = []

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

    def register_blueprint(self, blueprint, **options):
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

    # -------------------------------------------------------------------- #
    # Request Handling
    # -------------------------------------------------------------------- #

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
                    raise ServerError(
                        ("'None' was returned while requesting a "
                         "handler from the router"))

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

    def run(self, host="127.0.0.1", port=8000, debug=False, after_start=None,
            before_stop=None, sock=None, workers=1):
        """
        Runs the HTTP Server and listens until keyboard interrupt or term
        signal. On termination, drains connections before closing.
        :param host: Address to host on
        :param port: Port to host on
        :param debug: Enables debug output (slows server)
        :param after_start: Function to be executed after the server starts
        listening
        :param before_stop: Function to be executed when a stop signal is
        received before it is respected
        :param sock: Socket for the server to accept connections from
        :param workers: Number of processes
        received before it is respected
        :return: Nothing
        """
        self.error_handler.debug = True
        self.debug = debug

        server_settings = {
            'host': host,
            'port': port,
            'sock': sock,
            'debug': debug,
            'request_handler': self.handle_request,
            'request_timeout': self.config.REQUEST_TIMEOUT,
            'request_max_size': self.config.REQUEST_MAX_SIZE,
        }

        if debug:
            log.setLevel(logging.DEBUG)
        log.debug(self.config.LOGO)

        # Serve
        log.info('Goin\' Fast @ http://{}:{}'.format(host, port))

        try:
            if workers == 1:
                server_settings['after_start'] = after_start
                server_settings['before_stop'] = before_stop
                serve(**server_settings)
            else:
                log.info('Spinning up {} workers...'.format(workers))

                self.serve_multiple(server_settings, workers)

        except Exception as e:
            log.exception(
                'Experienced exception while trying to serve: {}'.format(e))
            pass

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
        for w in range(workers):
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
