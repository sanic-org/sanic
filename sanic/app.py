import logging
import re
import warnings
from asyncio import get_event_loop
from collections import deque, defaultdict
from functools import partial
from inspect import isawaitable, stack, getmodulename
from traceback import format_exc
from urllib.parse import urlencode, urlunparse

from sanic.config import Config
from sanic.constants import HTTP_METHODS
from sanic.exceptions import ServerError, URLBuildError, SanicException
from sanic.handlers import ErrorHandler
from sanic.log import log
from sanic.response import HTTPResponse
from sanic.router import Router
from sanic.server import serve, serve_multiple, HttpProtocol
from sanic.static import register as static_register
from sanic.testing import TestClient
from sanic.views import CompositionView


class Sanic:

    def __init__(self, name=None, router=None, error_handler=None):
        # Only set up a default log handler if the
        # end-user application didn't set anything up.
        if not logging.root.handlers and log.level == logging.NOTSET:
            formatter = logging.Formatter(
                "%(asctime)s: %(levelname)s: %(message)s")
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            log.addHandler(handler)
            log.setLevel(logging.INFO)

        # Get name from previous stack frame
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
        self.listeners = defaultdict(list)
        self.is_running = False

        # Register alternative method names
        self.go_fast = self.run

    @property
    def loop(self):
        """Synonymous with asyncio.get_event_loop().

        Only supported when using the `app.run` method.
        """
        if not self.is_running:
            raise SanicException(
                'Loop can only be retrieved after the app has started '
                'running. Not supported with `create_server` function')
        return get_event_loop()

    # -------------------------------------------------------------------- #
    # Registration
    # -------------------------------------------------------------------- #

    def add_task(self, task):
        """Schedule a task to run later, after the loop has started.
        Different from asyncio.ensure_future in that it does not
        also return a future, and the actual ensure_future call
        is delayed until before server start.

        :param task: future, couroutine or awaitable
        """
        @self.listener('before_server_start')
        def run(app, loop):
            if callable(task):
                loop.create_task(task())
            else:
                loop.create_task(task)

    # Decorator
    def listener(self, event):
        """Create a listener from a decorated function.

        :param event: event to listen to
        """
        def decorator(listener):
            self.listeners[event].append(listener)
            return listener
        return decorator

    # Decorator
    def route(self, uri, methods=frozenset({'GET'}), host=None):
        """Decorate a function to be registered as a route

        :param uri: path of the URL
        :param methods: list or tuple of methods allowed
        :param host:
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
        return self.route(uri, methods=frozenset({"DELETE"}), host=host)

    def add_route(self, handler, uri, methods=frozenset({'GET'}), host=None):
        """A helper method to register class instance or
        functions as a handler to the application url
        routes.

        :param handler: function or class instance
        :param uri: path of the URL
        :param methods: list or tuple of methods allowed, these are overridden
                        if using a HTTPMethodView
        :param host:
        :return: function or class instance
        """
        # Handle HTTPMethodView differently
        if hasattr(handler, 'view_class'):
            methods = set()

            for method in HTTP_METHODS:
                if getattr(handler.view_class, method.lower(), None):
                    methods.add(method)

        # handle composition view differently
        if isinstance(handler, CompositionView):
            methods = handler.handlers.keys()

        self.route(uri=uri, methods=methods, host=host)(handler)
        return handler

    def remove_route(self, uri, clean_cache=True, host=None):
        self.router.remove(uri, clean_cache, host)

    # Decorator
    def exception(self, *exceptions):
        """Decorate a function to be registered as a handler for exceptions

        :param exceptions: exceptions
        :return: decorated function
        """

        def response(handler):
            for exception in exceptions:
                self.error_handler.add(exception, handler)
            return handler

        return response

    # Decorator
    def middleware(self, middleware_or_request):
        """Decorate and register middleware to be called before a request.
        Can either be called as @app.middleware or @app.middleware('request')
        """
        def register_middleware(middleware, attach_to='request'):
            if attach_to == 'request':
                self.request_middleware.append(middleware)
            if attach_to == 'response':
                self.response_middleware.appendleft(middleware)
            return middleware

        # Detect which way this was called, @middleware or @middleware('AT')
        if callable(middleware_or_request):
            return register_middleware(middleware_or_request)

        else:
            return partial(register_middleware,
                           attach_to=middleware_or_request)

    # Static Files
    def static(self, uri, file_or_directory, pattern='.+',
               use_modified_since=True, use_content_range=False):
        """Register a root to serve files from. The input can either be a
        file or a directory. See
        """
        static_register(self, uri, file_or_directory, pattern,
                        use_modified_since, use_content_range)

    def blueprint(self, blueprint, **options):
        """Register a blueprint on the application.

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

    def url_for(self, view_name: str, **kwargs):
        """Build a URL based on a view name and the values provided.

        In order to build a URL, all request parameters must be supplied as
        keyword arguments, and each parameter must pass the test for the
        specified parameter type. If these conditions are not met, a
        `URLBuildError` will be thrown.

        Keyword arguments that are not request parameters will be included in
        the output URL's query string.

        :param view_name: string referencing the view name
        :param **kwargs: keys and values that are used to build request
            parameters and query string arguments.

        :return: the built URL

        Raises:
            URLBuildError
        """
        # find the route by the supplied view name
        uri, route = self.router.find_route_by_view_name(view_name)

        if not uri or not route:
            raise URLBuildError(
                    'Endpoint with name `{}` was not found'.format(
                        view_name))

        if uri != '/' and uri.endswith('/'):
            uri = uri[:-1]

        out = uri

        # find all the parameters we will need to build in the URL
        matched_params = re.findall(
            self.router.parameter_pattern, uri)

        # _method is only a placeholder now, don't know how to support it
        kwargs.pop('_method', None)
        anchor = kwargs.pop('_anchor', '')
        # _external need SERVER_NAME in config or pass _server arg
        external = kwargs.pop('_external', False)
        scheme = kwargs.pop('_scheme', '')
        if scheme and not external:
            raise ValueError('When specifying _scheme, _external must be True')

        netloc = kwargs.pop('_server', None)
        if netloc is None and external:
            netloc = self.config.get('SERVER_NAME', '')

        for match in matched_params:
            name, _type, pattern = self.router.parse_parameter_string(
                match)
            # we only want to match against each individual parameter
            specific_pattern = '^{}$'.format(pattern)
            supplied_param = None

            if kwargs.get(name):
                supplied_param = kwargs.get(name)
                del kwargs[name]
            else:
                raise URLBuildError(
                    'Required parameter `{}` was not passed to url_for'.format(
                        name))

            supplied_param = str(supplied_param)
            # determine if the parameter supplied by the caller passes the test
            # in the URL
            passes_pattern = re.match(specific_pattern, supplied_param)

            if not passes_pattern:
                if _type != str:
                    msg = (
                        'Value "{}" for parameter `{}` does not '
                        'match pattern for type `{}`: {}'.format(
                            supplied_param, name, _type.__name__, pattern))
                else:
                    msg = (
                        'Value "{}" for parameter `{}` '
                        'does not satisfy pattern {}'.format(
                            supplied_param, name, pattern))
                raise URLBuildError(msg)

            # replace the parameter in the URL with the supplied value
            replacement_regex = '(<{}.*?>)'.format(name)

            out = re.sub(
                replacement_regex, supplied_param, out)

        # parse the remainder of the keyword arguments into a querystring
        query_string = urlencode(kwargs, doseq=True) if kwargs else ''
        # scheme://netloc/path;parameters?query#fragment
        out = urlunparse((scheme, netloc, out, '', query_string, anchor))

        return out

    # -------------------------------------------------------------------- #
    # Request Handling
    # -------------------------------------------------------------------- #

    def converted_response_type(self, response):
        pass

    async def handle_request(self, request, response_callback):
        """Take a request from the HTTP Server and return a response object
        to be sent back The HTTP Server only expects a response object, so
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

            request.app = self

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
    # Testing
    # -------------------------------------------------------------------- #

    @property
    def test_client(self):
        return TestClient(self)

    # -------------------------------------------------------------------- #
    # Execution
    # -------------------------------------------------------------------- #

    def run(self, host="127.0.0.1", port=8000, debug=False, before_start=None,
            after_start=None, before_stop=None, after_stop=None, ssl=None,
            sock=None, workers=1, loop=None, protocol=HttpProtocol,
            backlog=100, stop_event=None, register_sys_signals=True):
        """Run the HTTP Server and listen until keyboard interrupt or term
        signal. On termination, drain connections before closing.

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
        :param loop:
        :param backlog:
        :param stop_event:
        :param register_sys_signals:
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
            self.is_running = True
            if workers == 1:
                serve(**server_settings)
            else:
                serve_multiple(server_settings, workers, stop_event)
        except:
            log.exception(
                'Experienced exception while trying to serve')
        finally:
            self.is_running = False
        log.info("Server Stopped")

    def stop(self):
        """This kills the Sanic"""
        get_event_loop().stop()

    async def create_server(self, host="127.0.0.1", port=8000, debug=False,
                            before_start=None, after_start=None,
                            before_stop=None, after_stop=None, ssl=None,
                            sock=None, loop=None, protocol=HttpProtocol,
                            backlog=100, stop_event=None):
        """Asynchronous version of `run`.

        NOTE: This does not support multiprocessing and is not the preferred
              way to run a Sanic application.
        """
        server_settings = self._helper(
            host=host, port=port, debug=debug, before_start=before_start,
            after_start=after_start, before_stop=before_stop,
            after_stop=after_stop, ssl=ssl, sock=sock,
            loop=loop or get_event_loop(), protocol=protocol,
            backlog=backlog, stop_event=stop_event,
            run_async=True)

        return await serve(**server_settings)

    def _helper(self, host="127.0.0.1", port=8000, debug=False,
                before_start=None, after_start=None, before_stop=None,
                after_stop=None, ssl=None, sock=None, workers=1, loop=None,
                protocol=HttpProtocol, backlog=100, stop_event=None,
                register_sys_signals=True, run_async=False):
        """Helper function used by `run` and `create_server`."""

        if loop is not None:
            if debug:
                warnings.simplefilter('default')
            warnings.warn("Passing a loop will be deprecated in version"
                          " 0.4.0 https://github.com/channelcat/sanic/"
                          "pull/335 has more information.",
                          DeprecationWarning)

        # Deprecate this
        if any(arg is not None for arg in (after_stop, after_start,
                                           before_start, before_stop)):
            if debug:
                warnings.simplefilter('default')
            warnings.warn("Passing a before_start, before_stop, after_start or"
                          "after_stop callback will be deprecated in next "
                          "major version after 0.4.0",
                          DeprecationWarning)

        self.error_handler.debug = debug
        self.debug = debug

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

        for event_name, settings_name, reverse, args in (
                ("before_server_start", "before_start", False, before_start),
                ("after_server_start", "after_start", False, after_start),
                ("before_server_stop", "before_stop", True, before_stop),
                ("after_server_stop", "after_stop", True, after_stop),
        ):
            listeners = self.listeners[event_name].copy()
            if args:
                if callable(args):
                    listeners.append(args)
                else:
                    listeners.extend(args)
            if reverse:
                listeners.reverse()
            # Prepend sanic to the arguments when listeners are triggered
            listeners = [partial(listener, self) for listener in listeners]
            server_settings[settings_name] = listeners

        if debug:
            log.setLevel(logging.DEBUG)
        if self.config.LOGO is not None:
            log.debug(self.config.LOGO)

        if run_async:
            server_settings['run_async'] = True

        # Serve
        proto = "http"
        if ssl is not None:
            proto = "https"
        log.info('Goin\' Fast @ {}://{}:{}'.format(proto, host, port))

        return server_settings
