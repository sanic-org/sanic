import logging
import logging.config
import os
import re
import warnings

from asyncio import CancelledError, Protocol, ensure_future, get_event_loop
from collections import defaultdict, deque
from functools import partial
from inspect import getmodulename, isawaitable, signature, stack
from socket import socket
from ssl import Purpose, SSLContext, create_default_context
from traceback import format_exc
from typing import Any, Dict, Optional, Type, Union
from urllib.parse import urlencode, urlunparse

from sanic import reloader_helpers
from sanic.asgi import ASGIApp
from sanic.blueprint_group import BlueprintGroup
from sanic.config import BASE_LOGO, Config
from sanic.constants import HTTP_METHODS
from sanic.exceptions import SanicException, ServerError, URLBuildError
from sanic.handlers import ErrorHandler
from sanic.log import LOGGING_CONFIG_DEFAULTS, error_logger, logger
from sanic.response import HTTPResponse, StreamingHTTPResponse
from sanic.router import Router
from sanic.server import (
    AsyncioServer,
    HttpProtocol,
    Signal,
    serve,
    serve_multiple,
)
from sanic.static import register as static_register
from sanic.testing import SanicASGITestClient, SanicTestClient
from sanic.views import CompositionView
from sanic.websocket import ConnectionClosed, WebSocketProtocol


class Sanic:
    def __init__(
        self,
        name=None,
        router=None,
        error_handler=None,
        load_env=True,
        request_class=None,
        strict_slashes=False,
        log_config=None,
        configure_logging=True,
    ):

        # Get name from previous stack frame
        if name is None:
            warnings.warn(
                "Sanic(name=None) is deprecated and None value support "
                "for `name` will be removed in the next release. "
                "Please use Sanic(name='your_application_name') instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            frame_records = stack()[1]
            name = getmodulename(frame_records[1])

        # logging
        if configure_logging:
            logging.config.dictConfig(log_config or LOGGING_CONFIG_DEFAULTS)

        self.name = name
        self.asgi = False
        self.router = router or Router()
        self.request_class = request_class
        self.error_handler = error_handler or ErrorHandler()
        self.config = Config(load_env=load_env)
        self.request_middleware = deque()
        self.response_middleware = deque()
        self.blueprints = {}
        self._blueprint_order = []
        self.configure_logging = configure_logging
        self.debug = None
        self.sock = None
        self.strict_slashes = strict_slashes
        self.listeners = defaultdict(list)
        self.is_running = False
        self.is_request_stream = False
        self.websocket_enabled = False
        self.websocket_tasks = set()
        self.named_request_middleware = {}
        self.named_response_middleware = {}
        # Register alternative method names
        self.go_fast = self.run

    @property
    def loop(self):
        """Synonymous with asyncio.get_event_loop().

        Only supported when using the `app.run` method.
        """
        if not self.is_running and self.asgi is False:
            raise SanicException(
                "Loop can only be retrieved after the app has started "
                "running. Not supported with `create_server` function"
            )
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
        try:
            if callable(task):
                try:
                    self.loop.create_task(task(self))
                except TypeError:
                    self.loop.create_task(task())
            else:
                self.loop.create_task(task)
        except SanicException:

            @self.listener("before_server_start")
            def run(app, loop):
                if callable(task):
                    try:
                        loop.create_task(task(self))
                    except TypeError:
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

    def register_listener(self, listener, event):
        """
        Register the listener for a given event.

        :param listener: callable i.e. setup_db(app, loop)
        :param event: when to register listener i.e. 'before_server_start'
        :return: listener
        """

        return self.listener(event)(listener)

    # Decorator
    def route(
        self,
        uri,
        methods=frozenset({"GET"}),
        host=None,
        strict_slashes=None,
        stream=False,
        version=None,
        name=None,
    ):
        """Decorate a function to be registered as a route

        :param uri: path of the URL
        :param methods: list or tuple of methods allowed
        :param host:
        :param strict_slashes:
        :param stream:
        :param version:
        :param name: user defined route name for url_for
        :return: tuple of routes, decorated function
        """

        # Fix case where the user did not prefix the URL with a /
        # and will probably get confused as to why it's not working
        if not uri.startswith("/"):
            uri = "/" + uri

        if stream:
            self.is_request_stream = True

        if strict_slashes is None:
            strict_slashes = self.strict_slashes

        def response(handler):
            args = list(signature(handler).parameters.keys())

            if not args:
                raise ValueError(
                    "Required parameter `request` missing "
                    "in the {0}() route?".format(handler.__name__)
                )

            if stream:
                handler.is_stream = stream

            routes = self.router.add(
                uri=uri,
                methods=methods,
                handler=handler,
                host=host,
                strict_slashes=strict_slashes,
                version=version,
                name=name,
            )
            return routes, handler

        return response

    # Shorthand method decorators
    def get(
        self, uri, host=None, strict_slashes=None, version=None, name=None
    ):
        """
        Add an API URL under the **GET** *HTTP* method

        :param uri: URL to be tagged to **GET** method of *HTTP*
        :param host: Host IP or FQDN for the service to use
        :param strict_slashes: Instruct :class:`Sanic` to check if the request
            URLs need to terminate with a */*
        :param version: API Version
        :param name: Unique name that can be used to identify the Route
        :return: Object decorated with :func:`route` method
        """
        return self.route(
            uri,
            methods=frozenset({"GET"}),
            host=host,
            strict_slashes=strict_slashes,
            version=version,
            name=name,
        )

    def post(
        self,
        uri,
        host=None,
        strict_slashes=None,
        stream=False,
        version=None,
        name=None,
    ):
        """
        Add an API URL under the **POST** *HTTP* method

        :param uri: URL to be tagged to **POST** method of *HTTP*
        :param host: Host IP or FQDN for the service to use
        :param strict_slashes: Instruct :class:`Sanic` to check if the request
            URLs need to terminate with a */*
        :param version: API Version
        :param name: Unique name that can be used to identify the Route
        :return: Object decorated with :func:`route` method
        """
        return self.route(
            uri,
            methods=frozenset({"POST"}),
            host=host,
            strict_slashes=strict_slashes,
            stream=stream,
            version=version,
            name=name,
        )

    def put(
        self,
        uri,
        host=None,
        strict_slashes=None,
        stream=False,
        version=None,
        name=None,
    ):
        """
        Add an API URL under the **PUT** *HTTP* method

        :param uri: URL to be tagged to **PUT** method of *HTTP*
        :param host: Host IP or FQDN for the service to use
        :param strict_slashes: Instruct :class:`Sanic` to check if the request
            URLs need to terminate with a */*
        :param version: API Version
        :param name: Unique name that can be used to identify the Route
        :return: Object decorated with :func:`route` method
        """
        return self.route(
            uri,
            methods=frozenset({"PUT"}),
            host=host,
            strict_slashes=strict_slashes,
            stream=stream,
            version=version,
            name=name,
        )

    def head(
        self, uri, host=None, strict_slashes=None, version=None, name=None
    ):
        return self.route(
            uri,
            methods=frozenset({"HEAD"}),
            host=host,
            strict_slashes=strict_slashes,
            version=version,
            name=name,
        )

    def options(
        self, uri, host=None, strict_slashes=None, version=None, name=None
    ):
        """
        Add an API URL under the **OPTIONS** *HTTP* method

        :param uri: URL to be tagged to **OPTIONS** method of *HTTP*
        :param host: Host IP or FQDN for the service to use
        :param strict_slashes: Instruct :class:`Sanic` to check if the request
            URLs need to terminate with a */*
        :param version: API Version
        :param name: Unique name that can be used to identify the Route
        :return: Object decorated with :func:`route` method
        """
        return self.route(
            uri,
            methods=frozenset({"OPTIONS"}),
            host=host,
            strict_slashes=strict_slashes,
            version=version,
            name=name,
        )

    def patch(
        self,
        uri,
        host=None,
        strict_slashes=None,
        stream=False,
        version=None,
        name=None,
    ):
        """
        Add an API URL under the **PATCH** *HTTP* method

        :param uri: URL to be tagged to **PATCH** method of *HTTP*
        :param host: Host IP or FQDN for the service to use
        :param strict_slashes: Instruct :class:`Sanic` to check if the request
            URLs need to terminate with a */*
        :param version: API Version
        :param name: Unique name that can be used to identify the Route
        :return: Object decorated with :func:`route` method
        """
        return self.route(
            uri,
            methods=frozenset({"PATCH"}),
            host=host,
            strict_slashes=strict_slashes,
            stream=stream,
            version=version,
            name=name,
        )

    def delete(
        self, uri, host=None, strict_slashes=None, version=None, name=None
    ):
        """
        Add an API URL under the **DELETE** *HTTP* method

        :param uri: URL to be tagged to **DELETE** method of *HTTP*
        :param host: Host IP or FQDN for the service to use
        :param strict_slashes: Instruct :class:`Sanic` to check if the request
            URLs need to terminate with a */*
        :param version: API Version
        :param name: Unique name that can be used to identify the Route
        :return: Object decorated with :func:`route` method
        """
        return self.route(
            uri,
            methods=frozenset({"DELETE"}),
            host=host,
            strict_slashes=strict_slashes,
            version=version,
            name=name,
        )

    def add_route(
        self,
        handler,
        uri,
        methods=frozenset({"GET"}),
        host=None,
        strict_slashes=None,
        version=None,
        name=None,
        stream=False,
    ):
        """A helper method to register class instance or
        functions as a handler to the application url
        routes.

        :param handler: function or class instance
        :param uri: path of the URL
        :param methods: list or tuple of methods allowed, these are overridden
                        if using a HTTPMethodView
        :param host:
        :param strict_slashes:
        :param version:
        :param name: user defined route name for url_for
        :param stream: boolean specifying if the handler is a stream handler
        :return: function or class instance
        """
        # Handle HTTPMethodView differently
        if hasattr(handler, "view_class"):
            methods = set()

            for method in HTTP_METHODS:
                _handler = getattr(handler.view_class, method.lower(), None)
                if _handler:
                    methods.add(method)
                    if hasattr(_handler, "is_stream"):
                        stream = True

        # handle composition view differently
        if isinstance(handler, CompositionView):
            methods = handler.handlers.keys()
            for _handler in handler.handlers.values():
                if hasattr(_handler, "is_stream"):
                    stream = True
                    break

        if strict_slashes is None:
            strict_slashes = self.strict_slashes

        self.route(
            uri=uri,
            methods=methods,
            host=host,
            strict_slashes=strict_slashes,
            stream=stream,
            version=version,
            name=name,
        )(handler)
        return handler

    # Decorator
    def websocket(
        self, uri, host=None, strict_slashes=None, subprotocols=None, name=None
    ):
        """
        Decorate a function to be registered as a websocket route

        :param uri: path of the URL
        :param host: Host IP or FQDN details
        :param strict_slashes: If the API endpoint needs to terminate
                               with a "/" or not
        :param subprotocols: optional list of str with supported subprotocols
        :param name: A unique name assigned to the URL so that it can
                     be used with :func:`url_for`
        :return: tuple of routes, decorated function
        """
        self.enable_websocket()

        # Fix case where the user did not prefix the URL with a /
        # and will probably get confused as to why it's not working
        if not uri.startswith("/"):
            uri = "/" + uri

        if strict_slashes is None:
            strict_slashes = self.strict_slashes

        def response(handler):
            async def websocket_handler(request, *args, **kwargs):
                request.app = self
                if not getattr(handler, "__blueprintname__", False):
                    request.endpoint = handler.__name__
                else:
                    request.endpoint = (
                        getattr(handler, "__blueprintname__", "")
                        + handler.__name__
                    )

                    pass

                if self.asgi:
                    ws = request.transport.get_websocket_connection()
                else:
                    try:
                        protocol = request.transport.get_protocol()
                    except AttributeError:
                        # On Python3.5 the Transport classes in asyncio do not
                        # have a get_protocol() method as in uvloop
                        protocol = request.transport._protocol
                    protocol.app = self

                    ws = await protocol.websocket_handshake(
                        request, subprotocols
                    )

                # schedule the application handler
                # its future is kept in self.websocket_tasks in case it
                # needs to be cancelled due to the server being stopped
                fut = ensure_future(handler(request, ws, *args, **kwargs))
                self.websocket_tasks.add(fut)
                try:
                    await fut
                except (CancelledError, ConnectionClosed):
                    pass
                finally:
                    self.websocket_tasks.remove(fut)
                await ws.close()

            routes = self.router.add(
                uri=uri,
                handler=websocket_handler,
                methods=frozenset({"GET"}),
                host=host,
                strict_slashes=strict_slashes,
                name=name,
            )
            return routes, handler

        return response

    def add_websocket_route(
        self,
        handler,
        uri,
        host=None,
        strict_slashes=None,
        subprotocols=None,
        name=None,
    ):
        """
        A helper method to register a function as a websocket route.

        :param handler: a callable function or instance of a class
                        that can handle the websocket request
        :param host: Host IP or FQDN details
        :param uri: URL path that will be mapped to the websocket
                    handler
                    handler
        :param strict_slashes: If the API endpoint needs to terminate
                with a "/" or not
        :param subprotocols: Subprotocols to be used with websocket
                handshake
        :param name: A unique name assigned to the URL so that it can
                be used with :func:`url_for`
        :return: Objected decorated by :func:`websocket`
        """
        if strict_slashes is None:
            strict_slashes = self.strict_slashes

        return self.websocket(
            uri,
            host=host,
            strict_slashes=strict_slashes,
            subprotocols=subprotocols,
            name=name,
        )(handler)

    def enable_websocket(self, enable=True):
        """Enable or disable the support for websocket.

        Websocket is enabled automatically if websocket routes are
        added to the application.
        """
        if not self.websocket_enabled:
            # if the server is stopped, we want to cancel any ongoing
            # websocket tasks, to allow the server to exit promptly
            @self.listener("before_server_stop")
            def cancel_websocket_tasks(app, loop):
                for task in self.websocket_tasks:
                    task.cancel()

        self.websocket_enabled = enable

    def remove_route(self, uri, clean_cache=True, host=None):
        """
        This method provides the app user a mechanism by which an already
        existing route can be removed from the :class:`Sanic` object

        .. warning::
            remove_route is deprecated in v19.06 and will be removed
            from future versions.

        :param uri: URL Path to be removed from the app
        :param clean_cache: Instruct sanic if it needs to clean up the LRU
            route cache
        :param host: IP address or FQDN specific to the host
        :return: None
        """
        warnings.warn(
            "remove_route is deprecated and will be removed "
            "from future versions.",
            DeprecationWarning,
            stacklevel=2,
        )
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

    def register_middleware(self, middleware, attach_to="request"):
        """
        Register an application level middleware that will be attached
        to all the API URLs registered under this application.

        This method is internally invoked by the :func:`middleware`
        decorator provided at the app level.

        :param middleware: Callback method to be attached to the
            middleware
        :param attach_to: The state at which the middleware needs to be
            invoked in the lifecycle of an *HTTP Request*.
            **request** - Invoke before the request is processed
            **response** - Invoke before the response is returned back
        :return: decorated method
        """
        if attach_to == "request":
            if middleware not in self.request_middleware:
                self.request_middleware.append(middleware)
        if attach_to == "response":
            if middleware not in self.response_middleware:
                self.response_middleware.appendleft(middleware)
        return middleware

    def register_named_middleware(
        self, middleware, route_names, attach_to="request"
    ):
        if attach_to == "request":
            for _rn in route_names:
                if _rn not in self.named_request_middleware:
                    self.named_request_middleware[_rn] = deque()
                if middleware not in self.named_request_middleware[_rn]:
                    self.named_request_middleware[_rn].append(middleware)
        if attach_to == "response":
            for _rn in route_names:
                if _rn not in self.named_response_middleware:
                    self.named_response_middleware[_rn] = deque()
                if middleware not in self.named_response_middleware[_rn]:
                    self.named_response_middleware[_rn].append(middleware)

    # Decorator
    def middleware(self, middleware_or_request):
        """
        Decorate and register middleware to be called before a request.
        Can either be called as *@app.middleware* or
        *@app.middleware('request')*

        :param: middleware_or_request: Optional parameter to use for
            identifying which type of middleware is being registered.
        """
        # Detect which way this was called, @middleware or @middleware('AT')
        if callable(middleware_or_request):
            return self.register_middleware(middleware_or_request)

        else:
            return partial(
                self.register_middleware, attach_to=middleware_or_request
            )

    # Static Files
    def static(
        self,
        uri,
        file_or_directory,
        pattern=r"/?.+",
        use_modified_since=True,
        use_content_range=False,
        stream_large_files=False,
        name="static",
        host=None,
        strict_slashes=None,
        content_type=None,
    ):
        """
        Register a root to serve files from. The input can either be a
        file or a directory. This method will enable an easy and simple way
        to setup the :class:`Route` necessary to serve the static files.

        :param uri: URL path to be used for serving static content
        :param file_or_directory: Path for the Static file/directory with
            static files
        :param pattern: Regex Pattern identifying the valid static files
        :param use_modified_since: If true, send file modified time, and return
            not modified if the browser's matches the server's
        :param use_content_range: If true, process header for range requests
            and sends the file part that is requested
        :param stream_large_files: If true, use the
            :func:`StreamingHTTPResponse.file_stream` handler rather
            than the :func:`HTTPResponse.file` handler to send the file.
            If this is an integer, this represents the threshold size to
            switch to :func:`StreamingHTTPResponse.file_stream`
        :param name: user defined name used for url_for
        :param host: Host IP or FQDN for the service to use
        :param strict_slashes: Instruct :class:`Sanic` to check if the request
            URLs need to terminate with a */*
        :param content_type: user defined content type for header
        :return: None
        """
        static_register(
            self,
            uri,
            file_or_directory,
            pattern,
            use_modified_since,
            use_content_range,
            stream_large_files,
            name,
            host,
            strict_slashes,
            content_type,
        )

    def blueprint(self, blueprint, **options):
        """Register a blueprint on the application.

        :param blueprint: Blueprint object or (list, tuple) thereof
        :param options: option dictionary with blueprint defaults
        :return: Nothing
        """
        if isinstance(blueprint, (list, tuple, BlueprintGroup)):
            for item in blueprint:
                self.blueprint(item, **options)
            return
        if blueprint.name in self.blueprints:
            assert self.blueprints[blueprint.name] is blueprint, (
                'A blueprint with the name "%s" is already registered.  '
                "Blueprint names must be unique." % (blueprint.name,)
            )
        else:
            self.blueprints[blueprint.name] = blueprint
            self._blueprint_order.append(blueprint)
        blueprint.register(self, options)

    def register_blueprint(self, *args, **kwargs):
        """
        Proxy method provided for invoking the :func:`blueprint` method

        .. note::
            To be deprecated in 1.0. Use :func:`blueprint` instead.

        :param args: Blueprint object or (list, tuple) thereof
        :param kwargs: option dictionary with blueprint defaults
        :return: None
        """

        if self.debug:
            warnings.simplefilter("default")
        warnings.warn(
            "Use of register_blueprint will be deprecated in "
            "version 1.0.  Please use the blueprint method"
            " instead",
            DeprecationWarning,
        )
        return self.blueprint(*args, **kwargs)

    def url_for(self, view_name: str, **kwargs):
        r"""Build a URL based on a view name and the values provided.

        In order to build a URL, all request parameters must be supplied as
        keyword arguments, and each parameter must pass the test for the
        specified parameter type. If these conditions are not met, a
        `URLBuildError` will be thrown.

        Keyword arguments that are not request parameters will be included in
        the output URL's query string.

        :param view_name: string referencing the view name
        :param \**kwargs: keys and values that are used to build request
            parameters and query string arguments.

        :return: the built URL

        Raises:
            URLBuildError
        """
        # find the route by the supplied view name
        kw: Dict[str, str] = {}
        # special static files url_for
        if view_name == "static":
            kw.update(name=kwargs.pop("name", "static"))
        elif view_name.endswith(".static"):  # blueprint.static
            kwargs.pop("name", None)
            kw.update(name=view_name)

        uri, route = self.router.find_route_by_view_name(view_name, **kw)
        if not (uri and route):
            raise URLBuildError(
                "Endpoint with name `{}` was not found".format(view_name)
            )

        if view_name == "static" or view_name.endswith(".static"):
            filename = kwargs.pop("filename", None)
            # it's static folder
            if "<file_uri:" in uri:
                folder_ = uri.split("<file_uri:", 1)[0]
                if folder_.endswith("/"):
                    folder_ = folder_[:-1]

                if filename.startswith("/"):
                    filename = filename[1:]

                uri = "{}/{}".format(folder_, filename)

        if uri != "/" and uri.endswith("/"):
            uri = uri[:-1]

        out = uri

        # find all the parameters we will need to build in the URL
        matched_params = re.findall(self.router.parameter_pattern, uri)

        # _method is only a placeholder now, don't know how to support it
        kwargs.pop("_method", None)
        anchor = kwargs.pop("_anchor", "")
        # _external need SERVER_NAME in config or pass _server arg
        external = kwargs.pop("_external", False)
        scheme = kwargs.pop("_scheme", "")
        if scheme and not external:
            raise ValueError("When specifying _scheme, _external must be True")

        netloc = kwargs.pop("_server", None)
        if netloc is None and external:
            netloc = self.config.get("SERVER_NAME", "")

        if external:
            if not scheme:
                if ":" in netloc[:8]:
                    scheme = netloc[:8].split(":", 1)[0]
                else:
                    scheme = "http"

            if "://" in netloc[:8]:
                netloc = netloc.split("://", 1)[-1]

        for match in matched_params:
            name, _type, pattern = self.router.parse_parameter_string(match)
            # we only want to match against each individual parameter
            specific_pattern = "^{}$".format(pattern)
            supplied_param = None

            if name in kwargs:
                supplied_param = kwargs.get(name)
                del kwargs[name]
            else:
                raise URLBuildError(
                    "Required parameter `{}` was not passed to url_for".format(
                        name
                    )
                )

            supplied_param = str(supplied_param)
            # determine if the parameter supplied by the caller passes the test
            # in the URL
            passes_pattern = re.match(specific_pattern, supplied_param)

            if not passes_pattern:
                if _type != str:
                    msg = (
                        'Value "{}" for parameter `{}` does not '
                        "match pattern for type `{}`: {}".format(
                            supplied_param, name, _type.__name__, pattern
                        )
                    )
                else:
                    msg = (
                        'Value "{}" for parameter `{}` '
                        "does not satisfy pattern {}".format(
                            supplied_param, name, pattern
                        )
                    )
                raise URLBuildError(msg)

            # replace the parameter in the URL with the supplied value
            replacement_regex = "(<{}.*?>)".format(name)

            out = re.sub(replacement_regex, supplied_param, out)

        # parse the remainder of the keyword arguments into a querystring
        query_string = urlencode(kwargs, doseq=True) if kwargs else ""
        # scheme://netloc/path;parameters?query#fragment
        out = urlunparse((scheme, netloc, out, "", query_string, anchor))

        return out

    # -------------------------------------------------------------------- #
    # Request Handling
    # -------------------------------------------------------------------- #

    def converted_response_type(self, response):
        """
        No implementation provided.
        """
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
        # Define `response` var here to remove warnings about
        # allocation before assignment below.
        response = None
        cancelled = False
        name = None
        try:
            # Fetch handler from router
            handler, args, kwargs, uri, name = self.router.get(request)

            # -------------------------------------------- #
            # Request Middleware
            # -------------------------------------------- #
            response = await self._run_request_middleware(
                request, request_name=name
            )
            # No middleware results
            if not response:
                # -------------------------------------------- #
                # Execute Handler
                # -------------------------------------------- #

                request.uri_template = uri
                if handler is None:
                    raise ServerError(
                        (
                            "'None' was returned while requesting a "
                            "handler from the router"
                        )
                    )
                else:
                    if not getattr(handler, "__blueprintname__", False):
                        request.endpoint = self._build_endpoint_name(
                            handler.__name__
                        )
                    else:
                        request.endpoint = self._build_endpoint_name(
                            getattr(handler, "__blueprintname__", ""),
                            handler.__name__,
                        )

                # Run response handler
                response = handler(request, *args, **kwargs)
                if isawaitable(response):
                    response = await response
        except CancelledError:
            # If response handler times out, the server handles the error
            # and cancels the handle_request job.
            # In this case, the transport is already closed and we cannot
            # issue a response.
            response = None
            cancelled = True
        except Exception as e:
            # -------------------------------------------- #
            # Response Generation Failed
            # -------------------------------------------- #

            try:
                response = self.error_handler.response(request, e)
                if isawaitable(response):
                    response = await response
            except Exception as e:
                if isinstance(e, SanicException):
                    response = self.error_handler.default(
                        request=request, exception=e
                    )
                elif self.debug:
                    response = HTTPResponse(
                        "Error while handling error: {}\nStack: {}".format(
                            e, format_exc()
                        ),
                        status=500,
                    )
                else:
                    response = HTTPResponse(
                        "An error occurred while handling an error", status=500
                    )
        finally:
            # -------------------------------------------- #
            # Response Middleware
            # -------------------------------------------- #
            # Don't run response middleware if response is None
            if response is not None:
                try:
                    response = await self._run_response_middleware(
                        request, response, request_name=name
                    )
                except CancelledError:
                    # Response middleware can timeout too, as above.
                    response = None
                    cancelled = True
                except BaseException:
                    error_logger.exception(
                        "Exception occurred in one of response "
                        "middleware handlers"
                    )
            if cancelled:
                raise CancelledError()

        # pass the response to the correct callback
        if write_callback is None or isinstance(
            response, StreamingHTTPResponse
        ):
            if stream_callback:
                await stream_callback(response)
            else:
                # Should only end here IF it is an ASGI websocket.
                # TODO:
                # - Add exception handling
                pass
        else:
            write_callback(response)

    # -------------------------------------------------------------------- #
    # Testing
    # -------------------------------------------------------------------- #

    @property
    def test_client(self):
        return SanicTestClient(self)

    @property
    def asgi_client(self):
        return SanicASGITestClient(self)

    # -------------------------------------------------------------------- #
    # Execution
    # -------------------------------------------------------------------- #

    def run(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        debug: bool = False,
        ssl: Union[dict, SSLContext, None] = None,
        sock: Optional[socket] = None,
        workers: int = 1,
        protocol: Type[Protocol] = None,
        backlog: int = 100,
        stop_event: Any = None,
        register_sys_signals: bool = True,
        access_log: Optional[bool] = None,
        **kwargs: Any
    ) -> None:
        """Run the HTTP Server and listen until keyboard interrupt or term
        signal. On termination, drain connections before closing.

        :param host: Address to host on
        :type host: str
        :param port: Port to host on
        :type port: int
        :param debug: Enables debug output (slows server)
        :type debug: bool
        :param ssl: SSLContext, or location of certificate and key
                    for SSL encryption of worker(s)
        :type ssl: SSLContext or dict
        :param sock: Socket for the server to accept connections from
        :type sock: socket
        :param workers: Number of processes received before it is respected
        :type workers: int
        :param protocol: Subclass of asyncio Protocol class
        :type protocol: type[Protocol]
        :param backlog: a number of unaccepted connections that the system
                        will allow before refusing new connections
        :type backlog: int
        :param stop_event: event to be triggered
                           before stopping the app - deprecated
        :type stop_event: None
        :param register_sys_signals: Register SIG* events
        :type register_sys_signals: bool
        :param access_log: Enables writing access logs (slows server)
        :type access_log: bool
        :return: Nothing
        """
        if "loop" in kwargs:
            raise TypeError(
                "loop is not a valid argument. To use an existing loop, "
                "change to create_server().\nSee more: "
                "https://sanic.readthedocs.io/en/latest/sanic/deploying.html"
                "#asynchronous-support"
            )

        # Default auto_reload to false
        auto_reload = False
        # If debug is set, default it to true (unless on windows)
        if debug and os.name == "posix":
            auto_reload = True
        # Allow for overriding either of the defaults
        auto_reload = kwargs.get("auto_reload", auto_reload)

        if sock is None:
            host, port = host or "127.0.0.1", port or 8000

        if protocol is None:
            protocol = (
                WebSocketProtocol if self.websocket_enabled else HttpProtocol
            )
        if stop_event is not None:
            if debug:
                warnings.simplefilter("default")
            warnings.warn(
                "stop_event will be removed from future versions.",
                DeprecationWarning,
            )
        # if access_log is passed explicitly change config.ACCESS_LOG
        if access_log is not None:
            self.config.ACCESS_LOG = access_log

        server_settings = self._helper(
            host=host,
            port=port,
            debug=debug,
            ssl=ssl,
            sock=sock,
            workers=workers,
            protocol=protocol,
            backlog=backlog,
            register_sys_signals=register_sys_signals,
            auto_reload=auto_reload,
        )

        try:
            self.is_running = True
            if workers == 1:
                if auto_reload and os.name != "posix":
                    # This condition must be removed after implementing
                    # auto reloader for other operating systems.
                    raise NotImplementedError

                if (
                    auto_reload
                    and os.environ.get("SANIC_SERVER_RUNNING") != "true"
                ):
                    reloader_helpers.watchdog(2)
                else:
                    serve(**server_settings)
            else:
                serve_multiple(server_settings, workers)
        except BaseException:
            error_logger.exception(
                "Experienced exception while trying to serve"
            )
            raise
        finally:
            self.is_running = False
        logger.info("Server Stopped")

    def stop(self):
        """This kills the Sanic"""
        get_event_loop().stop()

    async def create_server(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        debug: bool = False,
        ssl: Union[dict, SSLContext, None] = None,
        sock: Optional[socket] = None,
        protocol: Type[Protocol] = None,
        backlog: int = 100,
        stop_event: Any = None,
        access_log: Optional[bool] = None,
        return_asyncio_server=False,
        asyncio_server_kwargs=None,
    ) -> Optional[AsyncioServer]:
        """
        Asynchronous version of :func:`run`.

        This method will take care of the operations necessary to invoke
        the *before_start* events via :func:`trigger_events` method invocation
        before starting the *sanic* app in Async mode.

        .. note::
            This does not support multiprocessing and is not the preferred
            way to run a :class:`Sanic` application.

        :param host: Address to host on
        :type host: str
        :param port: Port to host on
        :type port: int
        :param debug: Enables debug output (slows server)
        :type debug: bool
        :param ssl: SSLContext, or location of certificate and key
                    for SSL encryption of worker(s)
        :type ssl: SSLContext or dict
        :param sock: Socket for the server to accept connections from
        :type sock: socket
        :param protocol: Subclass of asyncio Protocol class
        :type protocol: type[Protocol]
        :param backlog: a number of unaccepted connections that the system
                        will allow before refusing new connections
        :type backlog: int
        :param stop_event: event to be triggered
                           before stopping the app - deprecated
        :type stop_event: None
        :param access_log: Enables writing access logs (slows server)
        :type access_log: bool
        :param return_asyncio_server: flag that defines whether there's a need
                                      to return asyncio.Server or
                                      start it serving right away
        :type return_asyncio_server: bool
        :param asyncio_server_kwargs: key-value arguments for
                                      asyncio/uvloop create_server method
        :type asyncio_server_kwargs: dict
        :return: AsyncioServer if return_asyncio_server is true, else Nothing
        """

        if sock is None:
            host, port = host or "127.0.0.1", port or 8000

        if protocol is None:
            protocol = (
                WebSocketProtocol if self.websocket_enabled else HttpProtocol
            )
        if stop_event is not None:
            if debug:
                warnings.simplefilter("default")
            warnings.warn(
                "stop_event will be removed from future versions.",
                DeprecationWarning,
            )
        # if access_log is passed explicitly change config.ACCESS_LOG
        if access_log is not None:
            self.config.ACCESS_LOG = access_log

        server_settings = self._helper(
            host=host,
            port=port,
            debug=debug,
            ssl=ssl,
            sock=sock,
            loop=get_event_loop(),
            protocol=protocol,
            backlog=backlog,
            run_async=return_asyncio_server,
        )

        # Trigger before_start events
        await self.trigger_events(
            server_settings.get("before_start", []),
            server_settings.get("loop"),
        )

        return await serve(
            asyncio_server_kwargs=asyncio_server_kwargs, **server_settings
        )

    async def trigger_events(self, events, loop):
        """Trigger events (functions or async)
        :param events: one or more sync or async functions to execute
        :param loop: event loop
        """
        for event in events:
            result = event(loop)
            if isawaitable(result):
                await result

    async def _run_request_middleware(self, request, request_name=None):
        # The if improves speed.  I don't know why
        named_middleware = self.named_request_middleware.get(
            request_name, deque()
        )
        applicable_middleware = self.request_middleware + named_middleware
        if applicable_middleware:
            for middleware in applicable_middleware:
                response = middleware(request)
                if isawaitable(response):
                    response = await response
                if response:
                    return response
        return None

    async def _run_response_middleware(
        self, request, response, request_name=None
    ):
        named_middleware = self.named_response_middleware.get(
            request_name, deque()
        )
        applicable_middleware = self.response_middleware + named_middleware
        if applicable_middleware:
            for middleware in applicable_middleware:
                _response = middleware(request, response)
                if isawaitable(_response):
                    _response = await _response
                if _response:
                    response = _response
                    break
        return response

    def _helper(
        self,
        host=None,
        port=None,
        debug=False,
        ssl=None,
        sock=None,
        workers=1,
        loop=None,
        protocol=HttpProtocol,
        backlog=100,
        stop_event=None,
        register_sys_signals=True,
        run_async=False,
        auto_reload=False,
    ):
        """Helper function used by `run` and `create_server`."""
        if isinstance(ssl, dict):
            # try common aliaseses
            cert = ssl.get("cert") or ssl.get("certificate")
            key = ssl.get("key") or ssl.get("keyfile")
            if cert is None or key is None:
                raise ValueError("SSLContext or certificate and key required.")
            context = create_default_context(purpose=Purpose.CLIENT_AUTH)
            context.load_cert_chain(cert, keyfile=key)
            ssl = context
        if stop_event is not None:
            if debug:
                warnings.simplefilter("default")
            warnings.warn(
                "stop_event will be removed from future versions.",
                DeprecationWarning,
            )
        if self.config.PROXIES_COUNT and self.config.PROXIES_COUNT < 0:
            raise ValueError(
                "PROXIES_COUNT cannot be negative. "
                "https://sanic.readthedocs.io/en/latest/sanic/config.html"
                "#proxy-configuration"
            )

        self.error_handler.debug = debug
        self.debug = debug

        server_settings = {
            "protocol": protocol,
            "request_class": self.request_class,
            "is_request_stream": self.is_request_stream,
            "router": self.router,
            "host": host,
            "port": port,
            "sock": sock,
            "ssl": ssl,
            "app": self,
            "signal": Signal(),
            "debug": debug,
            "request_handler": self.handle_request,
            "error_handler": self.error_handler,
            "request_timeout": self.config.REQUEST_TIMEOUT,
            "response_timeout": self.config.RESPONSE_TIMEOUT,
            "keep_alive_timeout": self.config.KEEP_ALIVE_TIMEOUT,
            "request_max_size": self.config.REQUEST_MAX_SIZE,
            "request_buffer_queue_size": self.config.REQUEST_BUFFER_QUEUE_SIZE,
            "keep_alive": self.config.KEEP_ALIVE,
            "loop": loop,
            "register_sys_signals": register_sys_signals,
            "backlog": backlog,
            "access_log": self.config.ACCESS_LOG,
            "websocket_max_size": self.config.WEBSOCKET_MAX_SIZE,
            "websocket_max_queue": self.config.WEBSOCKET_MAX_QUEUE,
            "websocket_read_limit": self.config.WEBSOCKET_READ_LIMIT,
            "websocket_write_limit": self.config.WEBSOCKET_WRITE_LIMIT,
            "graceful_shutdown_timeout": self.config.GRACEFUL_SHUTDOWN_TIMEOUT,
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

        if self.configure_logging and debug:
            logger.setLevel(logging.DEBUG)

        if (
            self.config.LOGO
            and os.environ.get("SANIC_SERVER_RUNNING") != "true"
        ):
            logger.debug(
                self.config.LOGO
                if isinstance(self.config.LOGO, str)
                else BASE_LOGO
            )

        if run_async:
            server_settings["run_async"] = True

        # Serve
        if host and port and os.environ.get("SANIC_SERVER_RUNNING") != "true":
            proto = "http"
            if ssl is not None:
                proto = "https"
            logger.info("Goin' Fast @ {}://{}:{}".format(proto, host, port))

        return server_settings

    def _build_endpoint_name(self, *parts):
        parts = [self.name, *parts]
        return ".".join(parts)

    # -------------------------------------------------------------------- #
    # ASGI
    # -------------------------------------------------------------------- #

    async def __call__(self, scope, receive, send):
        """To be ASGI compliant, our instance must be a callable that accepts
        three arguments: scope, receive, send. See the ASGI reference for more
        details: https://asgi.readthedocs.io/en/latest/"""
        self.asgi = True
        asgi_app = await ASGIApp.create(self, scope, receive, send)
        await asgi_app()
