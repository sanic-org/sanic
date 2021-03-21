import logging
import logging.config
import os
import re

from asyncio import (
    CancelledError,
    Protocol,
    ensure_future,
    get_event_loop,
    wait_for,
)
from asyncio.futures import Future
from collections import defaultdict, deque
from functools import partial
from inspect import isawaitable
from socket import socket
from ssl import Purpose, SSLContext, create_default_context
from traceback import format_exc
from types import SimpleNamespace
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Deque,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Type,
    Union,
)
from urllib.parse import urlencode, urlunparse

from sanic_routing.exceptions import FinalizationError  # type: ignore
from sanic_routing.exceptions import NotFound  # type: ignore
from sanic_routing.route import Route  # type: ignore

from sanic import reloader_helpers
from sanic.asgi import ASGIApp
from sanic.base import BaseSanic
from sanic.blueprint_group import BlueprintGroup
from sanic.blueprints import Blueprint
from sanic.config import BASE_LOGO, Config
from sanic.exceptions import (
    InvalidUsage,
    SanicException,
    ServerError,
    URLBuildError,
)
from sanic.handlers import ErrorHandler
from sanic.log import LOGGING_CONFIG_DEFAULTS, error_logger, logger
from sanic.mixins.listeners import ListenerEvent
from sanic.models.futures import (
    FutureException,
    FutureListener,
    FutureMiddleware,
    FutureRoute,
    FutureSignal,
    FutureStatic,
)
from sanic.models.handler_types import ListenerType, MiddlewareType
from sanic.request import Request
from sanic.response import BaseHTTPResponse, HTTPResponse
from sanic.router import Router
from sanic.server import AsyncioServer, HttpProtocol
from sanic.server import Signal as ServerSignal
from sanic.server import serve, serve_multiple, serve_single
from sanic.signals import Signal, SignalRouter
from sanic.websocket import ConnectionClosed, WebSocketProtocol


class Sanic(BaseSanic):
    """
    The main application instance
    """

    __fake_slots__ = (
        "_app_registry",
        "_asgi_client",
        "_blueprint_order",
        "_future_routes",
        "_future_statics",
        "_future_middleware",
        "_future_listeners",
        "_future_exceptions",
        "_future_signals",
        "_test_client",
        "_test_manager",
        "asgi",
        "blueprints",
        "config",
        "configure_logging",
        "ctx",
        "debug",
        "error_handler",
        "go_fast",
        "is_running",
        "is_stopping",
        "listeners",
        "name",
        "named_request_middleware",
        "named_response_middleware",
        "request_class",
        "request_middleware",
        "response_middleware",
        "router",
        "signal_router",
        "sock",
        "strict_slashes",
        "test_mode",
        "websocket_enabled",
        "websocket_tasks",
    )

    _app_registry: Dict[str, "Sanic"] = {}
    test_mode = False

    def __init__(
        self,
        name: str = None,
        router: Optional[Router] = None,
        signal_router: Optional[SignalRouter] = None,
        error_handler: Optional[ErrorHandler] = None,
        load_env: bool = True,
        request_class: Optional[Type[Request]] = None,
        strict_slashes: bool = False,
        log_config: Optional[Dict[str, Any]] = None,
        configure_logging: bool = True,
        register: Optional[bool] = None,
        dumps: Optional[Callable[..., str]] = None,
    ) -> None:
        super().__init__()

        if name is None:
            raise SanicException(
                "Sanic instance cannot be unnamed. "
                "Please use Sanic(name='your_application_name') instead.",
            )
        # logging
        if configure_logging:
            logging.config.dictConfig(log_config or LOGGING_CONFIG_DEFAULTS)

        self._asgi_client = None
        self._blueprint_order: List[Blueprint] = []
        self._test_client = None
        self._test_manager = None
        self.asgi = False
        self.blueprints: Dict[str, Blueprint] = {}
        self.config = Config(load_env=load_env)
        self.configure_logging = configure_logging
        self.ctx = SimpleNamespace()
        self.debug = None
        self.error_handler = error_handler or ErrorHandler()
        self.is_running = False
        self.is_stopping = False
        self.listeners: Dict[str, List[ListenerType]] = defaultdict(list)
        self.name = name
        self.named_request_middleware: Dict[str, Deque[MiddlewareType]] = {}
        self.named_response_middleware: Dict[str, Deque[MiddlewareType]] = {}
        self.request_class = request_class
        self.request_middleware: Deque[MiddlewareType] = deque()
        self.response_middleware: Deque[MiddlewareType] = deque()
        self.router = router or Router()
        self.signal_router = signal_router or SignalRouter()
        self.sock = None
        self.strict_slashes = strict_slashes
        self.websocket_enabled = False
        self.websocket_tasks: Set[Future] = set()

        # Register alternative method names
        self.go_fast = self.run

        if register is not None:
            self.config.REGISTER = register

        if self.config.REGISTER:
            self.__class__.register_app(self)

        self.router.ctx.app = self

        if dumps:
            BaseHTTPResponse._dumps = dumps

    @property
    def loop(self):
        """
        Synonymous with asyncio.get_event_loop().

        .. note::

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

    def add_task(self, task) -> None:
        """
        Schedule a task to run later, after the loop has started.
        Different from asyncio.ensure_future in that it does not
        also return a future, and the actual ensure_future call
        is delayed until before server start.

        `See user guide re: background tasks
        <https://sanicframework.org/guide/basics/tasks.html#background-tasks>`__

        :param task: future, couroutine or awaitable
        """
        try:
            loop = self.loop  # Will raise SanicError if loop is not started
            self._loop_add_task(task, self, loop)
        except SanicException:
            self.listener("before_server_start")(
                partial(self._loop_add_task, task)
            )

    def register_listener(self, listener: Callable, event: str) -> Any:
        """
        Register the listener for a given event.

        :param listener: callable i.e. setup_db(app, loop)
        :param event: when to register listener i.e. 'before_server_start'
        :return: listener
        """

        try:
            _event = ListenerEvent(event)
        except ValueError:
            valid = ", ".join(ListenerEvent.__members__.values())
            raise InvalidUsage(f"Invalid event: {event}. Use one of: {valid}")

        self.listeners[_event].append(listener)
        return listener

    def register_middleware(self, middleware, attach_to: str = "request"):
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
        self,
        middleware,
        route_names: Iterable[str],
        attach_to: str = "request",
    ):
        """
        Method for attaching middleware to specific routes. This is mainly an
        internal tool for use by Blueprints to attach middleware to only its
        specfic routes. But, it could be used in a more generalized fashion.

        :param middleware: the middleware to execute
        :param route_names: a list of the names of the endpoints
        :type route_names: Iterable[str]
        :param attach_to: whether to attach to request or response,
            defaults to "request"
        :type attach_to: str, optional
        """
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
                    self.named_response_middleware[_rn].appendleft(middleware)
        return middleware

    def _apply_exception_handler(self, handler: FutureException):
        """Decorate a function to be registered as a handler for exceptions

        :param exceptions: exceptions
        :return: decorated function
        """

        for exception in handler.exceptions:
            if isinstance(exception, (tuple, list)):
                for e in exception:
                    self.error_handler.add(e, handler.handler)
            else:
                self.error_handler.add(exception, handler.handler)
        return handler.handler

    def _apply_listener(self, listener: FutureListener):
        return self.register_listener(listener.listener, listener.event)

    def _apply_route(self, route: FutureRoute) -> List[Route]:
        params = route._asdict()
        websocket = params.pop("websocket", False)
        subprotocols = params.pop("subprotocols", None)

        if websocket:
            self.enable_websocket()
            websocket_handler = partial(
                self._websocket_handler,
                route.handler,
                subprotocols=subprotocols,
            )
            websocket_handler.__name__ = route.handler.__name__  # type: ignore
            websocket_handler.is_websocket = True  # type: ignore
            params["handler"] = websocket_handler

        routes = self.router.add(**params)
        if isinstance(routes, Route):
            routes = [routes]
        for r in routes:
            r.ctx.websocket = websocket
            r.ctx.static = params.get("static", False)

        return routes

    def _apply_static(self, static: FutureStatic) -> Route:
        return self._register_static(static)

    def _apply_middleware(
        self,
        middleware: FutureMiddleware,
        route_names: Optional[List[str]] = None,
    ):
        if route_names:
            return self.register_named_middleware(
                middleware.middleware, route_names, middleware.attach_to
            )
        else:
            return self.register_middleware(
                middleware.middleware, middleware.attach_to
            )

    def _apply_signal(self, signal: FutureSignal) -> Signal:
        return self.signal_router.add(*signal)

    def dispatch(
        self,
        event: str,
        *,
        condition: Optional[Dict[str, str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Coroutine[Any, Any, Awaitable[Any]]:
        return self.signal_router.dispatch(
            event,
            context=context,
            condition=condition,
        )

    def event(self, event: str, timeout: Optional[Union[int, float]] = None):
        signal = self.signal_router.name_index.get(event)
        if not signal:
            raise NotFound("Could not find signal %s" % event)
        return wait_for(signal.ctx.event.wait(), timeout=timeout)

    def enable_websocket(self, enable=True):
        """Enable or disable the support for websocket.

        Websocket is enabled automatically if websocket routes are
        added to the application.
        """
        if not self.websocket_enabled:
            # if the server is stopped, we want to cancel any ongoing
            # websocket tasks, to allow the server to exit promptly
            self.listener("before_server_stop")(self._cancel_websocket_tasks)

        self.websocket_enabled = enable

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

        if (
            self.strict_slashes is not None
            and blueprint.strict_slashes is None
        ):
            blueprint.strict_slashes = self.strict_slashes
        blueprint.register(self, options)

    def url_for(self, view_name: str, **kwargs):
        """Build a URL based on a view name and the values provided.

        In order to build a URL, all request parameters must be supplied as
        keyword arguments, and each parameter must pass the test for the
        specified parameter type. If these conditions are not met, a
        `URLBuildError` will be thrown.

        Keyword arguments that are not request parameters will be included in
        the output URL's query string.

        There are several _special_ keyword arguments that will alter how the
        URL will be returned:

        1. **_anchor**: ``str`` - Adds an ``#anchor`` to the end
        2. **_scheme**: ``str`` - Should be either ``"http"`` or ``"https"``,
           default is ``"http"``
        3. **_external**: ``bool`` - Whether to return the path or a full URL
           with scheme and host
        4. **_host**: ``str`` - Used when one or more hosts are defined for a
           route to tell Sanic which to use
           (only applies with ``_external=True``)
        5. **_server**: ``str`` - If not using ``_host``, this will be used
           for defining the hostname of the URL
           (only applies with ``_external=True``),
           defaults to ``app.config.SERVER_NAME``

        If you want the PORT to appear in your URL, you should set it in:

        .. code-block::

            app.config.SERVER_NAME = "myserver:7777"

        `See user guide re: routing
        <https://sanicframework.org/guide/basics/routing.html#generating-a-url>`__

        :param view_name: string referencing the view name
        :param kwargs: keys and values that are used to build request
            parameters and query string arguments.

        :return: the built URL

        Raises:
            URLBuildError
        """
        # find the route by the supplied view name
        kw: Dict[str, str] = {}
        # special static files url_for

        if "." not in view_name:
            view_name = f"{self.name}.{view_name}"

        if view_name.endswith(".static"):
            name = kwargs.pop("name", None)
            if name:
                view_name = view_name.replace("static", name)
            kw.update(name=view_name)

        route = self.router.find_route_by_view_name(view_name, **kw)
        if not route:
            raise URLBuildError(
                f"Endpoint with name `{view_name}` was not found"
            )

        uri = route.path

        if getattr(route.ctx, "static", None):
            filename = kwargs.pop("filename", "")
            # it's static folder
            if "__file_uri__" in uri:
                folder_ = uri.split("<__file_uri__:", 1)[0]
                if folder_.endswith("/"):
                    folder_ = folder_[:-1]

                if filename.startswith("/"):
                    filename = filename[1:]

                kwargs["__file_uri__"] = filename

        if (
            uri != "/"
            and uri.endswith("/")
            and not route.strict
            and not route.raw_path[:-1]
        ):
            uri = uri[:-1]

        if not uri.startswith("/"):
            uri = f"/{uri}"

        out = uri

        # _method is only a placeholder now, don't know how to support it
        kwargs.pop("_method", None)
        anchor = kwargs.pop("_anchor", "")
        # _external need SERVER_NAME in config or pass _server arg
        host = kwargs.pop("_host", None)
        external = kwargs.pop("_external", False) or bool(host)
        scheme = kwargs.pop("_scheme", "")
        if route.ctx.hosts and external:
            if not host and len(route.ctx.hosts) > 1:
                raise ValueError(
                    f"Host is ambiguous: {', '.join(route.ctx.hosts)}"
                )
            elif host and host not in route.ctx.hosts:
                raise ValueError(
                    f"Requested host ({host}) is not available for this "
                    f"route: {route.ctx.hosts}"
                )
            elif not host:
                host = list(route.ctx.hosts)[0]

        if scheme and not external:
            raise ValueError("When specifying _scheme, _external must be True")

        netloc = kwargs.pop("_server", None)
        if netloc is None and external:
            netloc = host or self.config.get("SERVER_NAME", "")

        if external:
            if not scheme:
                if ":" in netloc[:8]:
                    scheme = netloc[:8].split(":", 1)[0]
                else:
                    scheme = "http"

            if "://" in netloc[:8]:
                netloc = netloc.split("://", 1)[-1]

        # find all the parameters we will need to build in the URL
        # matched_params = re.findall(self.router.parameter_pattern, uri)
        route.finalize()
        for param_info in route.params.values():
            # name, _type, pattern = self.router.parse_parameter_string(match)
            # we only want to match against each individual parameter

            try:
                supplied_param = str(kwargs.pop(param_info.name))
            except KeyError:
                raise URLBuildError(
                    f"Required parameter `{param_info.name}` was not "
                    "passed to url_for"
                )

            # determine if the parameter supplied by the caller
            # passes the test in the URL
            if param_info.pattern:
                passes_pattern = param_info.pattern.match(supplied_param)
                if not passes_pattern:
                    if param_info.cast != str:
                        msg = (
                            f'Value "{supplied_param}" '
                            f"for parameter `{param_info.name}` does "
                            "not match pattern for type "
                            f"`{param_info.cast.__name__}`: "
                            f"{param_info.pattern.pattern}"
                        )
                    else:
                        msg = (
                            f'Value "{supplied_param}" for parameter '
                            f"`{param_info.name}` does not satisfy "
                            f"pattern {param_info.pattern.pattern}"
                        )
                    raise URLBuildError(msg)

            # replace the parameter in the URL with the supplied value
            replacement_regex = f"(<{param_info.name}.*?>)"
            out = re.sub(replacement_regex, supplied_param, out)

        # parse the remainder of the keyword arguments into a querystring
        query_string = urlencode(kwargs, doseq=True) if kwargs else ""
        # scheme://netloc/path;parameters?query#fragment
        out = urlunparse((scheme, netloc, out, "", query_string, anchor))

        return out

    # -------------------------------------------------------------------- #
    # Request Handling
    # -------------------------------------------------------------------- #

    async def handle_exception(
        self, request: Request, exception: BaseException
    ):
        """
        A handler that catches specific exceptions and outputs a response.

        :param request: The current request object
        :type request: :class:`SanicASGITestClient`
        :param exception: The exception that was raised
        :type exception: BaseException
        :raises ServerError: response 500
        """
        # -------------------------------------------- #
        # Request Middleware
        # -------------------------------------------- #
        response = await self._run_request_middleware(
            request, request_name=None
        )
        # No middleware results
        if not response:
            try:
                response = self.error_handler.response(request, exception)
                if isawaitable(response):
                    response = await response
            except Exception as e:
                if isinstance(e, SanicException):
                    response = self.error_handler.default(request, e)
                elif self.debug:
                    response = HTTPResponse(
                        (
                            f"Error while handling error: {e}\n"
                            f"Stack: {format_exc()}"
                        ),
                        status=500,
                    )
                else:
                    response = HTTPResponse(
                        "An error occurred while handling an error", status=500
                    )
        if response is not None:
            try:
                response = await request.respond(response)
            except BaseException:
                # Skip response middleware
                if request.stream:
                    request.stream.respond(response)
                await response.send(end_stream=True)
                raise
        else:
            if request.stream:
                response = request.stream.response
        if isinstance(response, BaseHTTPResponse):
            await response.send(end_stream=True)
        else:
            raise ServerError(
                f"Invalid response type {response!r} (need HTTPResponse)"
            )

    async def handle_request(self, request: Request):
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
        try:
            # Fetch handler from router
            route, handler, kwargs = self.router.get(
                request.path, request.method, request.headers.get("host")
            )

            request._match_info = kwargs
            request.route = route

            if (
                request.stream.request_body  # type: ignore
                and not route.ctx.ignore_body
            ):

                if hasattr(handler, "is_stream"):
                    # Streaming handler: lift the size limit
                    request.stream.request_max_size = float(  # type: ignore
                        "inf"
                    )
                else:
                    # Non-streaming handler: preload body
                    await request.receive_body()

            # -------------------------------------------- #
            # Request Middleware
            # -------------------------------------------- #
            response = await self._run_request_middleware(
                request, request_name=route.name
            )

            # No middleware results
            if not response:
                # -------------------------------------------- #
                # Execute Handler
                # -------------------------------------------- #

                if handler is None:
                    raise ServerError(
                        (
                            "'None' was returned while requesting a "
                            "handler from the router"
                        )
                    )

                # Run response handler
                response = handler(request, **kwargs)
                if isawaitable(response):
                    response = await response

            if response:
                response = await request.respond(response)
            else:
                response = request.stream.response  # type: ignore
            # Make sure that response is finished / run StreamingHTTP callback

            if isinstance(response, BaseHTTPResponse):
                await response.send(end_stream=True)
            else:
                try:
                    # Fastest method for checking if the property exists
                    handler.is_websocket  # type: ignore
                except AttributeError:
                    raise ServerError(
                        f"Invalid response type {response!r} "
                        "(need HTTPResponse)"
                    )

        except CancelledError:
            raise
        except Exception as e:
            # Response Generation Failed
            await self.handle_exception(request, e)

    async def _websocket_handler(
        self, handler, request, *args, subprotocols=None, **kwargs
    ):
        request.app = self
        if not getattr(handler, "__blueprintname__", False):
            request._name = handler.__name__
        else:
            request._name = (
                getattr(handler, "__blueprintname__", "") + handler.__name__
            )

            pass

        if self.asgi:
            ws = request.transport.get_websocket_connection()
        else:
            protocol = request.transport.get_protocol()
            protocol.app = self

            ws = await protocol.websocket_handshake(request, subprotocols)

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

    # -------------------------------------------------------------------- #
    # Testing
    # -------------------------------------------------------------------- #

    @property
    def test_client(self):  # noqa
        if self._test_client:
            return self._test_client
        elif self._test_manager:
            return self._test_manager.test_client
        from sanic_testing.testing import SanicTestClient  # type: ignore

        self._test_client = SanicTestClient(self)
        return self._test_client

    @property
    def asgi_client(self):  # noqa
        """
        A testing client that uses ASGI to reach into the application to
        execute hanlers.

        :return: testing client
        :rtype: :class:`SanicASGITestClient`
        """
        if self._asgi_client:
            return self._asgi_client
        elif self._test_manager:
            return self._test_manager.asgi_client
        from sanic_testing.testing import SanicASGITestClient  # type: ignore

        self._asgi_client = SanicASGITestClient(self)
        return self._asgi_client

    # -------------------------------------------------------------------- #
    # Execution
    # -------------------------------------------------------------------- #

    def run(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        *,
        debug: bool = False,
        auto_reload: Optional[bool] = None,
        ssl: Union[dict, SSLContext, None] = None,
        sock: Optional[socket] = None,
        workers: int = 1,
        protocol: Optional[Type[Protocol]] = None,
        backlog: int = 100,
        register_sys_signals: bool = True,
        access_log: Optional[bool] = None,
        unix: Optional[str] = None,
        loop: None = None,
    ) -> None:
        """
        Run the HTTP Server and listen until keyboard interrupt or term
        signal. On termination, drain connections before closing.

        :param host: Address to host on
        :type host: str
        :param port: Port to host on
        :type port: int
        :param debug: Enables debug output (slows server)
        :type debug: bool
        :param auto_reload: Reload app whenever its source code is changed.
                            Enabled by default in debug mode.
        :type auto_relaod: bool
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
        :param register_sys_signals: Register SIG* events
        :type register_sys_signals: bool
        :param access_log: Enables writing access logs (slows server)
        :type access_log: bool
        :param unix: Unix socket to listen on instead of TCP port
        :type unix: str
        :return: Nothing
        """
        if loop is not None:
            raise TypeError(
                "loop is not a valid argument. To use an existing loop, "
                "change to create_server().\nSee more: "
                "https://sanic.readthedocs.io/en/latest/sanic/deploying.html"
                "#asynchronous-support"
            )

        if auto_reload or auto_reload is None and debug:
            if os.environ.get("SANIC_SERVER_RUNNING") != "true":
                return reloader_helpers.watchdog(1.0)

        if sock is None:
            host, port = host or "127.0.0.1", port or 8000

        if protocol is None:
            protocol = (
                WebSocketProtocol if self.websocket_enabled else HttpProtocol
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
            unix=unix,
            workers=workers,
            protocol=protocol,
            backlog=backlog,
            register_sys_signals=register_sys_signals,
            auto_reload=auto_reload,
        )

        try:
            self.is_running = True
            self.is_stopping = False
            if workers > 1 and os.name != "posix":
                logger.warn(
                    f"Multiprocessing is currently not supported on {os.name},"
                    " using workers=1 instead"
                )
                workers = 1
            if workers == 1:
                serve_single(server_settings)
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
        """
        This kills the Sanic
        """
        if not self.is_stopping:
            self.is_stopping = True
            get_event_loop().stop()

    async def create_server(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        *,
        debug: bool = False,
        ssl: Union[dict, SSLContext, None] = None,
        sock: Optional[socket] = None,
        protocol: Type[Protocol] = None,
        backlog: int = 100,
        access_log: Optional[bool] = None,
        unix: Optional[str] = None,
        return_asyncio_server: bool = False,
        asyncio_server_kwargs: Dict[str, Any] = None,
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
        # if access_log is passed explicitly change config.ACCESS_LOG
        if access_log is not None:
            self.config.ACCESS_LOG = access_log

        server_settings = self._helper(
            host=host,
            port=port,
            debug=debug,
            ssl=ssl,
            sock=sock,
            unix=unix,
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
        main_start = server_settings.pop("main_start", None)
        main_stop = server_settings.pop("main_stop", None)
        if main_start or main_stop:
            logger.warning(
                "Listener events for the main process are not available "
                "with create_server()"
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

        # request.request_middleware_started is meant as a stop-gap solution
        # until RFC 1630 is adopted
        if applicable_middleware and not request.request_middleware_started:
            request.request_middleware_started = True

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
                    if isinstance(response, BaseHTTPResponse):
                        response = request.stream.respond(response)
                    break
        return response

    def _helper(
        self,
        host=None,
        port=None,
        debug=False,
        ssl=None,
        sock=None,
        unix=None,
        workers=1,
        loop=None,
        protocol=HttpProtocol,
        backlog=100,
        register_sys_signals=True,
        run_async=False,
        auto_reload=False,
    ):
        """Helper function used by `run` and `create_server`."""

        self.listeners["before_server_start"] = [
            self.finalize
        ] + self.listeners["before_server_start"]

        if isinstance(ssl, dict):
            # try common aliaseses
            cert = ssl.get("cert") or ssl.get("certificate")
            key = ssl.get("key") or ssl.get("keyfile")
            if cert is None or key is None:
                raise ValueError("SSLContext or certificate and key required.")
            context = create_default_context(purpose=Purpose.CLIENT_AUTH)
            context.load_cert_chain(cert, keyfile=key)
            ssl = context
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
            "host": host,
            "port": port,
            "sock": sock,
            "unix": unix,
            "ssl": ssl,
            "app": self,
            "signal": ServerSignal(),
            "loop": loop,
            "register_sys_signals": register_sys_signals,
            "backlog": backlog,
        }

        # Register start/stop events

        for event_name, settings_name, reverse in (
            ("before_server_start", "before_start", False),
            ("after_server_start", "after_start", False),
            ("before_server_stop", "before_stop", True),
            ("after_server_stop", "after_stop", True),
            ("main_process_start", "main_start", False),
            ("main_process_stop", "main_stop", True),
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
        if host and port:
            proto = "http"
            if ssl is not None:
                proto = "https"
            if unix:
                logger.info(f"Goin' Fast @ {unix} {proto}://...")
            else:
                logger.info(f"Goin' Fast @ {proto}://{host}:{port}")

        return server_settings

    def _build_endpoint_name(self, *parts):
        parts = [self.name, *parts]
        return ".".join(parts)

    @classmethod
    def _loop_add_task(cls, task, app, loop):
        if callable(task):
            try:
                loop.create_task(task(app))
            except TypeError:
                loop.create_task(task())
        else:
            loop.create_task(task)

    @classmethod
    def _cancel_websocket_tasks(cls, app, loop):
        for task in app.websocket_tasks:
            task.cancel()

    # -------------------------------------------------------------------- #
    # ASGI
    # -------------------------------------------------------------------- #

    async def __call__(self, scope, receive, send):
        """
        To be ASGI compliant, our instance must be a callable that accepts
        three arguments: scope, receive, send. See the ASGI reference for more
        details: https://asgi.readthedocs.io/en/latest
        """
        self.asgi = True
        self._asgi_app = await ASGIApp.create(self, scope, receive, send)
        asgi_app = self._asgi_app
        await asgi_app()

    _asgi_single_callable = True  # We conform to ASGI 3.0 single-callable

    # -------------------------------------------------------------------- #
    # Configuration
    # -------------------------------------------------------------------- #

    def update_config(self, config: Union[bytes, str, dict, Any]):
        """
        Update app.config. Full implementation can be found in the user guide.

        `See user guide re: configuration
        <https://sanicframework.org/guide/deployment/configuration.html#basics>`__
        """

        self.config.update_config(config)

    # -------------------------------------------------------------------- #
    # Class methods
    # -------------------------------------------------------------------- #

    @classmethod
    def register_app(cls, app: "Sanic") -> None:
        """
        Register a Sanic instance
        """
        if not isinstance(app, cls):
            raise SanicException("Registered app must be an instance of Sanic")

        name = app.name
        if name in cls._app_registry and not cls.test_mode:
            raise SanicException(f'Sanic app name "{name}" already in use.')

        cls._app_registry[name] = app

    @classmethod
    def get_app(
        cls, name: Optional[str] = None, *, force_create: bool = False
    ) -> "Sanic":
        """
        Retrieve an instantiated Sanic instance
        """
        if name is None:
            if len(cls._app_registry) > 1:
                raise SanicException(
                    'Multiple Sanic apps found, use Sanic.get_app("app_name")'
                )
            elif len(cls._app_registry) == 0:
                raise SanicException("No Sanic apps have been registered.")
            else:
                return list(cls._app_registry.values())[0]
        try:
            return cls._app_registry[name]
        except KeyError:
            if force_create:
                return cls(name)
            raise SanicException(f'Sanic app name "{name}" not found.')

    # -------------------------------------------------------------------- #
    # Static methods
    # -------------------------------------------------------------------- #

    @staticmethod
    async def finalize(app, _):
        try:
            app.router.finalize()
            if app.signal_router.routes:
                app.signal_router.finalize()  # noqa
        except FinalizationError as e:
            if not Sanic.test_mode:
                raise e  # noqa
