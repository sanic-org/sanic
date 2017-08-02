import logging
import logging.config
import re
import warnings
from asyncio import get_event_loop, ensure_future, CancelledError
from collections import deque, defaultdict
from functools import partial
from inspect import isawaitable, stack, getmodulename
from traceback import format_exc
from urllib.parse import urlencode, urlunparse
from ssl import create_default_context, Purpose

from sanic.config import Config, LOGGING
from sanic.constants import HTTP_METHODS
from sanic.exceptions import ServerError, URLBuildError, SanicException
from sanic.handlers import ErrorHandler
from sanic.log import log
from sanic.response import HTTPResponse, StreamingHTTPResponse
from sanic.router import Router
from sanic.server import serve, serve_multiple, HttpProtocol, Signal
from sanic.static import register as static_register
from sanic.testing import SanicTestClient
from sanic.views import CompositionView
from sanic.websocket import WebSocketProtocol, ConnectionClosed


class Sanic:

    def __init__(self, name=None, router=None, error_handler=None,
                 load_env=True, request_class=None,
                 log_config=LOGGING):
        if log_config:
            logging.config.dictConfig(log_config)
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
        self.request_class = request_class
        self.error_handler = error_handler or ErrorHandler()
        self.config = Config(load_env=load_env)
        self.log_config = log_config
        self.request_middleware = deque()
        self.response_middleware = deque()
        self.blueprints = {}
        self._blueprint_order = []
        self.debug = None
        self.sock = None
        self.listeners = defaultdict(list)
        self.is_running = False
        self.is_request_stream = False
        self.websocket_enabled = False
        self.websocket_tasks = []

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
    def route(self, uri, methods=frozenset({'GET'}), host=None,
              strict_slashes=False, stream=False, version=None):
        """Decorate a function to be registered as a route

        :param uri: path of the URL
        :param methods: list or tuple of methods allowed
        :param host:
        :param strict_slashes:
        :param stream:
        :return: decorated function
        """

        # Fix case where the user did not prefix the URL with a /
        # and will probably get confused as to why it's not working
        if not uri.startswith('/'):
            uri = '/' + uri

        if stream:
            self.is_request_stream = True

        def response(handler):
            if stream:
                handler.is_stream = stream
            self.router.add(uri=uri, methods=methods, handler=handler,
                            host=host, strict_slashes=strict_slashes,
                            version=version)
            return handler

        return response

    # Shorthand method decorators
    def get(self, uri, host=None, strict_slashes=False, version=None):
        return self.route(uri, methods=frozenset({"GET"}), host=host,
                          strict_slashes=strict_slashes, version=version)

    def post(self, uri, host=None, strict_slashes=False, stream=False,
             version=None):
        return self.route(uri, methods=frozenset({"POST"}), host=host,
                          strict_slashes=strict_slashes, stream=stream,
                          version=version)

    def put(self, uri, host=None, strict_slashes=False, stream=False,
            version=None):
        return self.route(uri, methods=frozenset({"PUT"}), host=host,
                          strict_slashes=strict_slashes, stream=stream,
                          version=version)

    def head(self, uri, host=None, strict_slashes=False, version=None):
        return self.route(uri, methods=frozenset({"HEAD"}), host=host,
                          strict_slashes=strict_slashes, version=version)

    def options(self, uri, host=None, strict_slashes=False, version=None):
        return self.route(uri, methods=frozenset({"OPTIONS"}), host=host,
                          strict_slashes=strict_slashes, version=version)

    def patch(self, uri, host=None, strict_slashes=False, stream=False,
              version=None):
        return self.route(uri, methods=frozenset({"PATCH"}), host=host,
                          strict_slashes=strict_slashes, stream=stream,
                          version=version)

    def delete(self, uri, host=None, strict_slashes=False, version=None):
        return self.route(uri, methods=frozenset({"DELETE"}), host=host,
                          strict_slashes=strict_slashes, version=version)

    def add_route(self, handler, uri, methods=frozenset({'GET'}), host=None,
                  strict_slashes=False, version=None):
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
        stream = False
        # Handle HTTPMethodView differently
        if hasattr(handler, 'view_class'):
            methods = set()

            for method in HTTP_METHODS:
                _handler = getattr(handler.view_class, method.lower(), None)
                if _handler:
                    methods.add(method)
                    if hasattr(_handler, 'is_stream'):
                        stream = True

        # handle composition view differently
        if isinstance(handler, CompositionView):
            methods = handler.handlers.keys()
            for _handler in handler.handlers.values():
                if hasattr(_handler, 'is_stream'):
                    stream = True
                    break

        self.route(uri=uri, methods=methods, host=host,
                   strict_slashes=strict_slashes, stream=stream,
                   version=version)(handler)
        return handler

    # Decorator
    def websocket(self, uri, host=None, strict_slashes=False):
        """Decorate a function to be registered as a websocket route
        :param uri: path of the URL
        :param host:
        :return: decorated function
        """
        self.enable_websocket()

        # Fix case where the user did not prefix the URL with a /
        # and will probably get confused as to why it's not working
        if not uri.startswith('/'):
            uri = '/' + uri

        def response(handler):
            async def websocket_handler(request, *args, **kwargs):
                request.app = self
                try:
                    protocol = request.transport.get_protocol()
                except AttributeError:
                    # On Python3.5 the Transport classes in asyncio do not
                    # have a get_protocol() method as in uvloop
                    protocol = request.transport._protocol
                ws = await protocol.websocket_handshake(request)

                # schedule the application handler
                # its future is kept in self.websocket_tasks in case it
                # needs to be cancelled due to the server being stopped
                fut = ensure_future(handler(request, ws, *args, **kwargs))
                self.websocket_tasks.append(fut)
                try:
                    await fut
                except (CancelledError, ConnectionClosed):
                    pass
                self.websocket_tasks.remove(fut)
                await ws.close()

            self.router.add(uri=uri, handler=websocket_handler,
                            methods=frozenset({'GET'}), host=host,
                            strict_slashes=strict_slashes)
            return handler

        return response

    def add_websocket_route(self, handler, uri, host=None,
                            strict_slashes=False):
        """A helper method to register a function as a websocket route."""
        return self.websocket(uri, host=host,
                              strict_slashes=strict_slashes)(handler)

    def enable_websocket(self, enable=True):
        """Enable or disable the support for websocket.

        Websocket is enabled automatically if websocket routes are
        added to the application.
        """
        if not self.websocket_enabled:
            # if the server is stopped, we want to cancel any ongoing
            # websocket tasks, to allow the server to exit promptly
            @self.listener('before_server_stop')
            def cancel_websocket_tasks(app, loop):
                for task in self.websocket_tasks:
                    task.cancel()

        self.websocket_enabled = enable

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
                if isinstance(exception, (tuple, list)):
                    for e in exception:
                        self.error_handler.add(e, handler)
                else:
                    self.error_handler.add(exception, handler)
            return handler

        return response

    def register_middleware(self, middleware, attach_to='request'):
        if attach_to == 'request':
            self.request_middleware.append(middleware)
        if attach_to == 'response':
            self.response_middleware.appendleft(middleware)
        return middleware

    # Decorator
    def middleware(self, middleware_or_request):
        """Decorate and register middleware to be called before a request.
        Can either be called as @app.middleware or @app.middleware('request')
        """

        # Detect which way this was called, @middleware or @middleware('AT')
        if callable(middleware_or_request):
            return self.register_middleware(middleware_or_request)

        else:
            return partial(self.register_middleware,
                           attach_to=middleware_or_request)

    # Static Files
    def static(self, uri, file_or_directory, pattern=r'/?.+',
               use_modified_since=True, use_content_range=False,
               stream_large_files=False):
        """Register a root to serve files from. The input can either be a
        file or a directory. See
        """
        static_register(self, uri, file_or_directory, pattern,
                        use_modified_since, use_content_range,
                        stream_large_files)

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
        :param \*\*kwargs: keys and values that are used to build request
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

    async def handle_request(self, request, write_callback, stream_callback):
        """Take a request from the HTTP Server and return a response object
        to be sent back The HTTP Server only expects a response object, so
        exception handling must be done here

        :param request: HTTP Request object
        :param write_callback: Synchronous response function to be
            called with the response as the only argument
        :param stream_callback: Coroutine that handles streaming a
            StreamingHTTPResponse if produced by the handler.

        :return: Nothing
        """
        try:
            # -------------------------------------------- #
            # Request Middleware
            # -------------------------------------------- #

            request.app = self
            response = await self._run_request_middleware(request)
            # No middleware results
            if not response:
                # -------------------------------------------- #
                # Execute Handler
                # -------------------------------------------- #

                # Fetch handler from router
                handler, args, kwargs, uri = self.router.get(request)
                request.uri_template = uri
                if handler is None:
                    raise ServerError(
                        ("'None' was returned while requesting a "
                         "handler from the router"))

                # Run response handler
                response = handler(request, *args, **kwargs)
                if isawaitable(response):
                    response = await response
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
        finally:
            # -------------------------------------------- #
            # Response Middleware
            # -------------------------------------------- #
            try:
                response = await self._run_response_middleware(request,
                                                               response)
            except:
                log.exception(
                    'Exception occured in one of response middleware handlers'
                )

        # pass the response to the correct callback
        if isinstance(response, StreamingHTTPResponse):
            await stream_callback(response)
        else:
            write_callback(response)

    # -------------------------------------------------------------------- #
    # Testing
    # -------------------------------------------------------------------- #

    @property
    def test_client(self):
        return SanicTestClient(self)

    # -------------------------------------------------------------------- #
    # Execution
    # -------------------------------------------------------------------- #

    def run(self, host=None, port=None, debug=False, ssl=None,
            sock=None, workers=1, protocol=None,
            backlog=100, stop_event=None, register_sys_signals=True,
            log_config=None):
        """Run the HTTP Server and listen until keyboard interrupt or term
        signal. On termination, drain connections before closing.

        :param host: Address to host on
        :param port: Port to host on
        :param debug: Enables debug output (slows server)
        :param ssl: SSLContext, or location of certificate and key
                            for SSL encryption of worker(s)
        :param sock: Socket for the server to accept connections from
        :param workers: Number of processes
                            received before it is respected
        :param backlog:
        :param stop_event:
        :param register_sys_signals:
        :param protocol: Subclass of asyncio protocol class
        :return: Nothing
        """
        if sock is None:
            host, port = host or "127.0.0.1", port or 8000

        if log_config:
            self.log_config = log_config
            logging.config.dictConfig(log_config)
        if protocol is None:
            protocol = (WebSocketProtocol if self.websocket_enabled
                        else HttpProtocol)
        if stop_event is not None:
            if debug:
                warnings.simplefilter('default')
            warnings.warn("stop_event will be removed from future versions.",
                          DeprecationWarning)
        server_settings = self._helper(
            host=host, port=port, debug=debug, ssl=ssl, sock=sock,
            workers=workers, protocol=protocol, backlog=backlog,
            register_sys_signals=register_sys_signals,
            has_log=self.log_config is not None)

        try:
            self.is_running = True
            if workers == 1:
                serve(**server_settings)
            else:
                serve_multiple(server_settings, workers)
        except:
            log.exception(
                'Experienced exception while trying to serve')
            raise
        finally:
            self.is_running = False
        log.info("Server Stopped")

    def stop(self):
        """This kills the Sanic"""
        get_event_loop().stop()

    def __call__(self):
        """gunicorn compatibility"""
        return self

    async def create_server(self, host=None, port=None, debug=False,
                            ssl=None, sock=None, protocol=None,
                            backlog=100, stop_event=None,
                            log_config=LOGGING):
        """Asynchronous version of `run`.

        NOTE: This does not support multiprocessing and is not the preferred
              way to run a Sanic application.
        """
        if sock is None:
            host, port = host or "127.0.0.1", port or 8000

        if log_config:
            logging.config.dictConfig(log_config)
        if protocol is None:
            protocol = (WebSocketProtocol if self.websocket_enabled
                        else HttpProtocol)
        if stop_event is not None:
            if debug:
                warnings.simplefilter('default')
            warnings.warn("stop_event will be removed from future versions.",
                          DeprecationWarning)
        server_settings = self._helper(
            host=host, port=port, debug=debug, ssl=ssl, sock=sock,
            loop=get_event_loop(), protocol=protocol,
            backlog=backlog, run_async=True,
            has_log=log_config is not None)

        return await serve(**server_settings)

    async def _run_request_middleware(self, request):
        # The if improves speed.  I don't know why
        if self.request_middleware:
            for middleware in self.request_middleware:
                response = middleware(request)
                if isawaitable(response):
                    response = await response
                if response:
                    return response
        return None

    async def _run_response_middleware(self, request, response):
        if self.response_middleware:
            for middleware in self.response_middleware:
                _response = middleware(request, response)
                if isawaitable(_response):
                    _response = await _response
                if _response:
                    response = _response
                    break
        return response

    def _helper(self, host=None, port=None, debug=False,
                ssl=None, sock=None, workers=1, loop=None,
                protocol=HttpProtocol, backlog=100, stop_event=None,
                register_sys_signals=True, run_async=False, has_log=True):
        """Helper function used by `run` and `create_server`."""
        if isinstance(ssl, dict):
            # try common aliaseses
            cert = ssl.get('cert') or ssl.get('certificate')
            key = ssl.get('key') or ssl.get('keyfile')
            if cert is None or key is None:
                raise ValueError("SSLContext or certificate and key required.")
            context = create_default_context(purpose=Purpose.CLIENT_AUTH)
            context.load_cert_chain(cert, keyfile=key)
            ssl = context
        if stop_event is not None:
            if debug:
                warnings.simplefilter('default')
            warnings.warn("stop_event will be removed from future versions.",
                          DeprecationWarning)

        self.error_handler.debug = debug
        self.debug = debug

        server_settings = {
            'protocol': protocol,
            'request_class': self.request_class,
            'is_request_stream': self.is_request_stream,
            'router': self.router,
            'host': host,
            'port': port,
            'sock': sock,
            'ssl': ssl,
            'signal': Signal(),
            'debug': debug,
            'request_handler': self.handle_request,
            'error_handler': self.error_handler,
            'request_timeout': self.config.REQUEST_TIMEOUT,
            'request_max_size': self.config.REQUEST_MAX_SIZE,
            'keep_alive': self.config.KEEP_ALIVE,
            'loop': loop,
            'register_sys_signals': register_sys_signals,
            'backlog': backlog,
            'has_log': has_log,
            'websocket_max_size': self.config.WEBSOCKET_MAX_SIZE,
            'websocket_max_queue': self.config.WEBSOCKET_MAX_QUEUE,
            'graceful_shutdown_timeout': self.config.GRACEFUL_SHUTDOWN_TIMEOUT
        }

        # -------------------------------------------- #
        # Register start/stop events
        # -------------------------------------------- #

        for event_name, settings_name, reverse in (
                ("before_server_start", "before_start", False),
                ("after_server_start", "after_start", False),
                ("before_server_stop", "before_stop", True),
                ("after_server_stop", "after_stop", True),
        ):
            listeners = self.listeners[event_name].copy()
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
        if host and port:
            proto = "http"
            if ssl is not None:
                proto = "https"
            log.info('Goin\' Fast @ {}://{}:{}'.format(proto, host, port))

        return server_settings
