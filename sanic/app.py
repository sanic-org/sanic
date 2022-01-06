from __future__ import annotations

import asyncio
import logging
import logging.config
import os
import platform
import re
import sys

from asyncio import (
    AbstractEventLoop,
    CancelledError,
    Protocol,
    Task,
    ensure_future,
    get_event_loop,
    wait_for,
)
from asyncio.futures import Future
from collections import defaultdict, deque
from functools import partial
from importlib import import_module
from inspect import isawaitable
from pathlib import Path
from socket import socket
from ssl import SSLContext
from traceback import format_exc
from types import SimpleNamespace
from typing import (
    TYPE_CHECKING,
    Any,
    AnyStr,
    Awaitable,
    Callable,
    Coroutine,
    Deque,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from urllib.parse import urlencode, urlunparse
from warnings import filterwarnings

from sanic_routing.exceptions import (  # type: ignore
    FinalizationError,
    NotFound,
)
from sanic_routing.route import Route  # type: ignore

from sanic import reloader_helpers
from sanic.application.ext import setup_ext
from sanic.application.logo import get_logo
from sanic.application.motd import MOTD
from sanic.application.state import ApplicationState, Mode
from sanic.asgi import ASGIApp
from sanic.base.root import BaseSanic
from sanic.blueprint_group import BlueprintGroup
from sanic.blueprints import Blueprint
from sanic.compat import OS_IS_WINDOWS, enable_windows_color_support
from sanic.config import SANIC_PREFIX, Config
from sanic.exceptions import (
    InvalidUsage,
    SanicException,
    ServerError,
    URLBuildError,
)
from sanic.handlers import ErrorHandler
from sanic.helpers import _default
from sanic.http import Stage
from sanic.log import (
    LOGGING_CONFIG_DEFAULTS,
    Colors,
    deprecation,
    error_logger,
    logger,
)
from sanic.mixins.listeners import ListenerEvent
from sanic.models.futures import (
    FutureException,
    FutureListener,
    FutureMiddleware,
    FutureRegistry,
    FutureRoute,
    FutureSignal,
    FutureStatic,
)
from sanic.models.handler_types import ListenerType, MiddlewareType
from sanic.models.handler_types import Sanic as SanicVar
from sanic.request import Request
from sanic.response import BaseHTTPResponse, HTTPResponse, ResponseStream
from sanic.router import Router
from sanic.server import AsyncioServer, HttpProtocol
from sanic.server import Signal as ServerSignal
from sanic.server import serve, serve_multiple, serve_single, try_use_uvloop
from sanic.server.protocols.websocket_protocol import WebSocketProtocol
from sanic.server.websockets.impl import ConnectionClosed
from sanic.signals import Signal, SignalRouter
from sanic.tls import process_to_context
from sanic.touchup import TouchUp, TouchUpMeta


if TYPE_CHECKING:  # no cov
    try:
        from sanic_ext import Extend  # type: ignore
        from sanic_ext.extensions.base import Extension  # type: ignore
    except ImportError:
        Extend = TypeVar("Extend")  # type: ignore


if OS_IS_WINDOWS:
    enable_windows_color_support()

filterwarnings("once", category=DeprecationWarning)

SANIC_PACKAGES = ("sanic-routing", "sanic-testing", "sanic-ext")


class Sanic(BaseSanic, metaclass=TouchUpMeta):
    """
    The main application instance
    """

    __touchup__ = (
        "handle_request",
        "handle_exception",
        "_run_response_middleware",
        "_run_request_middleware",
    )
    __slots__ = (
        "_asgi_app",
        "_asgi_client",
        "_blueprint_order",
        "_delayed_tasks",
        "_ext",
        "_future_exceptions",
        "_future_listeners",
        "_future_middleware",
        "_future_registry",
        "_future_routes",
        "_future_signals",
        "_future_statics",
        "_state",
        "_task_registry",
        "_test_client",
        "_test_manager",
        "blueprints",
        "config",
        "configure_logging",
        "ctx",
        "error_handler",
        "go_fast",
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
        "websocket_enabled",
        "websocket_tasks",
    )

    _app_registry: Dict[str, "Sanic"] = {}
    _uvloop_setting = None  # TODO: Remove in v22.6
    test_mode = False

    def __init__(
        self,
        name: str = None,
        config: Optional[Config] = None,
        ctx: Optional[Any] = None,
        router: Optional[Router] = None,
        signal_router: Optional[SignalRouter] = None,
        error_handler: Optional[ErrorHandler] = None,
        env_prefix: Optional[str] = SANIC_PREFIX,
        request_class: Optional[Type[Request]] = None,
        strict_slashes: bool = False,
        log_config: Optional[Dict[str, Any]] = None,
        configure_logging: bool = True,
        register: Optional[bool] = None,
        dumps: Optional[Callable[..., AnyStr]] = None,
    ) -> None:
        super().__init__(name=name)

        # logging
        if configure_logging:
            dict_config = log_config or LOGGING_CONFIG_DEFAULTS
            logging.config.dictConfig(dict_config)  # type: ignore

        if config and env_prefix != SANIC_PREFIX:
            raise SanicException(
                "When instantiating Sanic with config, you cannot also pass "
                "env_prefix"
            )

        # First setup config
        self.config: Config = config or Config(env_prefix=env_prefix)

        # Then we can do the rest
        self._asgi_client: Any = None
        self._blueprint_order: List[Blueprint] = []
        self._delayed_tasks: List[str] = []
        self._future_registry: FutureRegistry = FutureRegistry()
        self._state: ApplicationState = ApplicationState(app=self)
        self._task_registry: Dict[str, Task] = {}
        self._test_client: Any = None
        self._test_manager: Any = None
        self.asgi = False
        self.auto_reload = False
        self.blueprints: Dict[str, Blueprint] = {}
        self.configure_logging: bool = configure_logging
        self.ctx: Any = ctx or SimpleNamespace()
        self.debug = False
        self.error_handler: ErrorHandler = error_handler or ErrorHandler()
        self.listeners: Dict[str, List[ListenerType[Any]]] = defaultdict(list)
        self.named_request_middleware: Dict[str, Deque[MiddlewareType]] = {}
        self.named_response_middleware: Dict[str, Deque[MiddlewareType]] = {}
        self.request_class: Type[Request] = request_class or Request
        self.request_middleware: Deque[MiddlewareType] = deque()
        self.response_middleware: Deque[MiddlewareType] = deque()
        self.router: Router = router or Router()
        self.signal_router: SignalRouter = signal_router or SignalRouter()
        self.sock: Optional[socket] = None
        self.strict_slashes: bool = strict_slashes
        self.websocket_enabled: bool = False
        self.websocket_tasks: Set[Future[Any]] = set()

        # Register alternative method names
        self.go_fast = self.run

        if register is not None:
            deprecation(
                "The register argument is deprecated and will stop working "
                "in v22.6. After v22.6 all apps will be added to the Sanic "
                "app registry.",
                22.6,
            )
            self.config.REGISTER = register
        if self.config.REGISTER:
            self.__class__.register_app(self)

        self.router.ctx.app = self
        self.signal_router.ctx.app = self

        if dumps:
            BaseHTTPResponse._dumps = dumps  # type: ignore

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

    def register_listener(
        self, listener: ListenerType[SanicVar], event: str
    ) -> ListenerType[SanicVar]:
        """
        Register the listener for a given event.

        :param listener: callable i.e. setup_db(app, loop)
        :param event: when to register listener i.e. 'before_server_start'
        :return: listener
        """

        try:
            _event = ListenerEvent[event.upper()]
        except (ValueError, AttributeError):
            valid = ", ".join(
                map(lambda x: x.lower(), ListenerEvent.__members__.keys())
            )
            raise InvalidUsage(f"Invalid event: {event}. Use one of: {valid}")

        if "." in _event:
            self.signal(_event.value)(
                partial(self._listener, listener=listener)
            )
        else:
            self.listeners[_event.value].append(listener)

        return listener

    def register_middleware(
        self, middleware: MiddlewareType, attach_to: str = "request"
    ) -> MiddlewareType:
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
        middleware: MiddlewareType,
        route_names: Iterable[str],
        attach_to: str = "request",
    ):
        """
        Method for attaching middleware to specific routes. This is mainly an
        internal tool for use by Blueprints to attach middleware to only its
        specific routes. But, it could be used in a more generalized fashion.

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

    def _apply_exception_handler(
        self,
        handler: FutureException,
        route_names: Optional[List[str]] = None,
    ):
        """Decorate a function to be registered as a handler for exceptions

        :param exceptions: exceptions
        :return: decorated function
        """

        for exception in handler.exceptions:
            if isinstance(exception, (tuple, list)):
                for e in exception:
                    self.error_handler.add(e, handler.handler, route_names)
            else:
                self.error_handler.add(exception, handler.handler, route_names)
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

        ctx = params.pop("route_context")

        routes = self.router.add(**params)
        if isinstance(routes, Route):
            routes = [routes]

        for r in routes:
            r.ctx.websocket = websocket
            r.ctx.static = params.get("static", False)
            r.ctx.__dict__.update(ctx)

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
        fail_not_found: bool = True,
        inline: bool = False,
        reverse: bool = False,
    ) -> Coroutine[Any, Any, Awaitable[Any]]:
        return self.signal_router.dispatch(
            event,
            context=context,
            condition=condition,
            inline=inline,
            reverse=reverse,
            fail_not_found=fail_not_found,
        )

    async def event(
        self, event: str, timeout: Optional[Union[int, float]] = None
    ):
        signal = self.signal_router.name_index.get(event)
        if not signal:
            if self.config.EVENT_AUTOREGISTER:
                self.signal_router.reset()
                self.add_signal(None, event)
                signal = self.signal_router.name_index[event]
                self.signal_router.finalize()
            else:
                raise NotFound("Could not find signal %s" % event)
        return await wait_for(signal.ctx.event.wait(), timeout=timeout)

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

    def blueprint(
        self,
        blueprint: Union[
            Blueprint, List[Blueprint], Tuple[Blueprint], BlueprintGroup
        ],
        **options: Any,
    ):
        """Register a blueprint on the application.

        :param blueprint: Blueprint object or (list, tuple) thereof
        :param options: option dictionary with blueprint defaults
        :return: Nothing
        """
        if isinstance(blueprint, (list, tuple, BlueprintGroup)):
            for item in blueprint:
                params = {**options}
                if isinstance(blueprint, BlueprintGroup):
                    if blueprint.url_prefix:
                        merge_from = [
                            options.get("url_prefix", ""),
                            blueprint.url_prefix,
                        ]
                        if not isinstance(item, BlueprintGroup):
                            merge_from.append(item.url_prefix or "")
                        merged_prefix = "/".join(
                            u.strip("/") for u in merge_from
                        ).rstrip("/")
                        params["url_prefix"] = f"/{merged_prefix}"

                    for _attr in ["version", "strict_slashes"]:
                        if getattr(item, _attr) is None:
                            params[_attr] = getattr(
                                blueprint, _attr
                            ) or options.get(_attr)
                    if item.version_prefix == "/v":
                        if blueprint.version_prefix == "/v":
                            params["version_prefix"] = options.get(
                                "version_prefix"
                            )
                        else:
                            params["version_prefix"] = blueprint.version_prefix
                self.blueprint(item, **params)
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
                pattern = (
                    param_info.pattern[1]
                    if isinstance(param_info.pattern, tuple)
                    else param_info.pattern
                )
                passes_pattern = pattern.match(supplied_param)
                if not passes_pattern:
                    if param_info.cast != str:
                        msg = (
                            f'Value "{supplied_param}" '
                            f"for parameter `{param_info.name}` does "
                            "not match pattern for type "
                            f"`{param_info.cast.__name__}`: "
                            f"{pattern.pattern}"
                        )
                    else:
                        msg = (
                            f'Value "{supplied_param}" for parameter '
                            f"`{param_info.name}` does not satisfy "
                            f"pattern {pattern.pattern}"
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
    ):  # no cov
        """
        A handler that catches specific exceptions and outputs a response.

        :param request: The current request object
        :param exception: The exception that was raised
        :raises ServerError: response 500
        """
        await self.dispatch(
            "http.lifecycle.exception",
            inline=True,
            context={"request": request, "exception": exception},
        )

        if (
            request.stream is not None
            and request.stream.stage is not Stage.HANDLER
        ):
            error_logger.exception(exception, exc_info=True)
            logger.error(
                "The error response will not be sent to the client for "
                f'the following exception:"{exception}". A previous response '
                "has at least partially been sent."
            )

            # ----------------- deprecated -----------------
            handler = self.error_handler._lookup(
                exception, request.name if request else None
            )
            if handler:
                deprecation(
                    "An error occurred while handling the request after at "
                    "least some part of the response was sent to the client. "
                    "Therefore, the response from your custom exception "
                    f"handler {handler.__name__} will not be sent to the "
                    "client. Beginning in v22.6, Sanic will stop executing "
                    "custom exception handlers in this scenario. Exception "
                    "handlers should only be used to generate the exception "
                    "responses. If you would like to perform any other "
                    "action on a raised exception, please consider using a "
                    "signal handler like "
                    '`@app.signal("http.lifecycle.exception")`\n'
                    "For further information, please see the docs: "
                    "https://sanicframework.org/en/guide/advanced/"
                    "signals.html",
                    22.6,
                )
                try:
                    response = self.error_handler.response(request, exception)
                    if isawaitable(response):
                        response = await response
                except BaseException as e:
                    logger.error("An error occurred in the exception handler.")
                    error_logger.exception(e)
            # ----------------------------------------------

            return

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
                request.reset_response()
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

        # Marked for cleanup and DRY with handle_request/handle_exception
        # when ResponseStream is no longer supporder
        if isinstance(response, BaseHTTPResponse):
            await self.dispatch(
                "http.lifecycle.response",
                inline=True,
                context={
                    "request": request,
                    "response": response,
                },
            )
            await response.send(end_stream=True)
        elif isinstance(response, ResponseStream):
            resp = await response(request)
            await self.dispatch(
                "http.lifecycle.response",
                inline=True,
                context={
                    "request": request,
                    "response": resp,
                },
            )
            await response.eof()
        else:
            raise ServerError(
                f"Invalid response type {response!r} (need HTTPResponse)"
            )

    async def handle_request(self, request: Request):  # no cov
        """Take a request from the HTTP Server and return a response object
        to be sent back The HTTP Server only expects a response object, so
        exception handling must be done here

        :param request: HTTP Request object
        :return: Nothing
        """
        await self.dispatch(
            "http.lifecycle.handle",
            inline=True,
            context={"request": request},
        )

        # Define `response` var here to remove warnings about
        # allocation before assignment below.
        response = None
        try:

            await self.dispatch(
                "http.routing.before",
                inline=True,
                context={"request": request},
            )
            # Fetch handler from router
            route, handler, kwargs = self.router.get(
                request.path,
                request.method,
                request.headers.getone("host", None),
            )

            request._match_info = {**kwargs}
            request.route = route

            await self.dispatch(
                "http.routing.after",
                inline=True,
                context={
                    "request": request,
                    "route": route,
                    "kwargs": kwargs,
                    "handler": handler,
                },
            )

            if (
                request.stream
                and request.stream.request_body
                and not route.ctx.ignore_body
            ):

                if hasattr(handler, "is_stream"):
                    # Streaming handler: lift the size limit
                    request.stream.request_max_size = float("inf")
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
                response = handler(request, **request.match_info)
                if isawaitable(response):
                    response = await response

            if request.responded:
                if response is not None:
                    error_logger.error(
                        "The response object returned by the route handler "
                        "will not be sent to client. The request has already "
                        "been responded to."
                    )
                if request.stream is not None:
                    response = request.stream.response
            elif response is not None:
                response = await request.respond(response)
            elif not hasattr(handler, "is_websocket"):
                response = request.stream.response  # type: ignore

            # Marked for cleanup and DRY with handle_request/handle_exception
            # when ResponseStream is no longer supporder
            if isinstance(response, BaseHTTPResponse):
                await self.dispatch(
                    "http.lifecycle.response",
                    inline=True,
                    context={
                        "request": request,
                        "response": response,
                    },
                )
                await response.send(end_stream=True)
            elif isinstance(response, ResponseStream):
                resp = await response(request)
                await self.dispatch(
                    "http.lifecycle.response",
                    inline=True,
                    context={
                        "request": request,
                        "response": resp,
                    },
                )
                await response.eof()
            else:
                if not hasattr(handler, "is_websocket"):
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
        if self.asgi:
            ws = request.transport.get_websocket_connection()
            await ws.accept(subprotocols)
        else:
            protocol = request.transport.get_protocol()
            ws = await protocol.websocket_handshake(request, subprotocols)

        # schedule the application handler
        # its future is kept in self.websocket_tasks in case it
        # needs to be cancelled due to the server being stopped
        fut = ensure_future(handler(request, ws, *args, **kwargs))
        self.websocket_tasks.add(fut)
        cancelled = False
        try:
            await fut
        except Exception as e:
            self.error_handler.log(request, e)
        except (CancelledError, ConnectionClosed):
            cancelled = True
        finally:
            self.websocket_tasks.remove(fut)
            if cancelled:
                ws.end_connection(1000)
            else:
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

    def make_coffee(self, *args, **kwargs):
        self.state.coffee = True
        self.run(*args, **kwargs)

    def run(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        *,
        debug: bool = False,
        auto_reload: Optional[bool] = None,
        ssl: Union[None, SSLContext, dict, str, list, tuple] = None,
        sock: Optional[socket] = None,
        workers: int = 1,
        protocol: Optional[Type[Protocol]] = None,
        backlog: int = 100,
        register_sys_signals: bool = True,
        access_log: Optional[bool] = None,
        unix: Optional[str] = None,
        loop: AbstractEventLoop = None,
        reload_dir: Optional[Union[List[str], str]] = None,
        noisy_exceptions: Optional[bool] = None,
        motd: bool = True,
        fast: bool = False,
        verbosity: int = 0,
        motd_display: Optional[Dict[str, str]] = None,
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
        :type ssl: str, dict, SSLContext or list
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
        :param noisy_exceptions: Log exceptions that are normally considered
                                 to be quiet/silent
        :type noisy_exceptions: bool
        :return: Nothing
        """
        self.state.verbosity = verbosity

        if fast and workers != 1:
            raise RuntimeError("You cannot use both fast=True and workers=X")

        if motd_display:
            self.config.MOTD_DISPLAY.update(motd_display)

        if reload_dir:
            if isinstance(reload_dir, str):
                reload_dir = [reload_dir]

            for directory in reload_dir:
                direc = Path(directory)
                if not direc.is_dir():
                    logger.warning(
                        f"Directory {directory} could not be located"
                    )
                self.state.reload_dirs.add(Path(directory))

        if loop is not None:
            raise TypeError(
                "loop is not a valid argument. To use an existing loop, "
                "change to create_server().\nSee more: "
                "https://sanic.readthedocs.io/en/latest/sanic/deploying.html"
                "#asynchronous-support"
            )

        if auto_reload or auto_reload is None and debug:
            auto_reload = True
            if os.environ.get("SANIC_SERVER_RUNNING") != "true":
                return reloader_helpers.watchdog(1.0, self)

        if sock is None:
            host, port = host or "127.0.0.1", port or 8000

        if protocol is None:
            protocol = (
                WebSocketProtocol if self.websocket_enabled else HttpProtocol
            )

        # Set explicitly passed configuration values
        for attribute, value in {
            "ACCESS_LOG": access_log,
            "AUTO_RELOAD": auto_reload,
            "MOTD": motd,
            "NOISY_EXCEPTIONS": noisy_exceptions,
        }.items():
            if value is not None:
                setattr(self.config, attribute, value)

        if fast:
            self.state.fast = True
            try:
                workers = len(os.sched_getaffinity(0))
            except AttributeError:
                workers = os.cpu_count() or 1

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
        )

        if self.config.USE_UVLOOP is True or (
            self.config.USE_UVLOOP is _default and not OS_IS_WINDOWS
        ):
            try_use_uvloop()

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
            self.shutdown_tasks(timeout=0)
            self.is_stopping = True
            get_event_loop().stop()

    async def create_server(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        *,
        debug: bool = False,
        ssl: Union[None, SSLContext, dict, str, list, tuple] = None,
        sock: Optional[socket] = None,
        protocol: Type[Protocol] = None,
        backlog: int = 100,
        access_log: Optional[bool] = None,
        unix: Optional[str] = None,
        return_asyncio_server: bool = False,
        asyncio_server_kwargs: Dict[str, Any] = None,
        noisy_exceptions: Optional[bool] = None,
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
        :param noisy_exceptions: Log exceptions that are normally considered
                                 to be quiet/silent
        :type noisy_exceptions: bool
        :return: AsyncioServer if return_asyncio_server is true, else Nothing
        """

        if sock is None:
            host, port = host or "127.0.0.1", port or 8000

        if protocol is None:
            protocol = (
                WebSocketProtocol if self.websocket_enabled else HttpProtocol
            )

        # Set explicitly passed configuration values
        for attribute, value in {
            "ACCESS_LOG": access_log,
            "NOISY_EXCEPTIONS": noisy_exceptions,
        }.items():
            if value is not None:
                setattr(self.config, attribute, value)

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

        if self.config.USE_UVLOOP is not _default:
            error_logger.warning(
                "You are trying to change the uvloop configuration, but "
                "this is only effective when using the run(...) method. "
                "When using the create_server(...) method Sanic will use "
                "the already existing loop."
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

    async def _run_request_middleware(
        self, request, request_name=None
    ):  # no cov
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
                await self.dispatch(
                    "http.middleware.before",
                    inline=True,
                    context={
                        "request": request,
                        "response": None,
                    },
                    condition={"attach_to": "request"},
                )

                response = middleware(request)
                if isawaitable(response):
                    response = await response

                await self.dispatch(
                    "http.middleware.after",
                    inline=True,
                    context={
                        "request": request,
                        "response": None,
                    },
                    condition={"attach_to": "request"},
                )

                if response:
                    return response
        return None

    async def _run_response_middleware(
        self, request, response, request_name=None
    ):  # no cov
        named_middleware = self.named_response_middleware.get(
            request_name, deque()
        )
        applicable_middleware = self.response_middleware + named_middleware
        if applicable_middleware:
            for middleware in applicable_middleware:
                await self.dispatch(
                    "http.middleware.before",
                    inline=True,
                    context={
                        "request": request,
                        "response": response,
                    },
                    condition={"attach_to": "response"},
                )

                _response = middleware(request, response)
                if isawaitable(_response):
                    _response = await _response

                await self.dispatch(
                    "http.middleware.after",
                    inline=True,
                    context={
                        "request": request,
                        "response": _response if _response else response,
                    },
                    condition={"attach_to": "response"},
                )

                if _response:
                    response = _response
                    if isinstance(response, BaseHTTPResponse):
                        response = request.stream.respond(response)
                    break
        return response

    def _helper(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        debug: bool = False,
        ssl: Union[None, SSLContext, dict, str, list, tuple] = None,
        sock: Optional[socket] = None,
        unix: Optional[str] = None,
        workers: int = 1,
        loop: AbstractEventLoop = None,
        protocol: Type[Protocol] = HttpProtocol,
        backlog: int = 100,
        register_sys_signals: bool = True,
        run_async: bool = False,
    ):
        """Helper function used by `run` and `create_server`."""
        if self.config.PROXIES_COUNT and self.config.PROXIES_COUNT < 0:
            raise ValueError(
                "PROXIES_COUNT cannot be negative. "
                "https://sanic.readthedocs.io/en/latest/sanic/config.html"
                "#proxy-configuration"
            )

        ssl = process_to_context(ssl)

        self.debug = debug
        self.state.host = host
        self.state.port = port
        self.state.workers = workers
        self.state.ssl = ssl
        self.state.unix = unix
        self.state.sock = sock

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

        self.motd(self.serve_location)

        if sys.stdout.isatty() and not self.state.is_debug:
            error_logger.warning(
                f"{Colors.YELLOW}Sanic is running in PRODUCTION mode. "
                "Consider using '--debug' or '--dev' while actively "
                f"developing your application.{Colors.END}"
            )

        # Register start/stop events
        for event_name, settings_name, reverse in (
            ("main_process_start", "main_start", False),
            ("main_process_stop", "main_stop", True),
        ):
            listeners = self.listeners[event_name].copy()
            if reverse:
                listeners.reverse()
            # Prepend sanic to the arguments when listeners are triggered
            listeners = [partial(listener, self) for listener in listeners]
            server_settings[settings_name] = listeners  # type: ignore

        if run_async:
            server_settings["run_async"] = True

        return server_settings

    @property
    def serve_location(self) -> str:
        serve_location = ""
        proto = "http"
        if self.state.ssl is not None:
            proto = "https"
        if self.state.unix:
            serve_location = f"{self.state.unix} {proto}://..."
        elif self.state.sock:
            serve_location = f"{self.state.sock.getsockname()} {proto}://..."
        elif self.state.host and self.state.port:
            # colon(:) is legal for a host only in an ipv6 address
            display_host = (
                f"[{self.state.host}]"
                if ":" in self.state.host
                else self.state.host
            )
            serve_location = f"{proto}://{display_host}:{self.state.port}"

        return serve_location

    def _build_endpoint_name(self, *parts):
        parts = [self.name, *parts]
        return ".".join(parts)

    @classmethod
    def _cancel_websocket_tasks(cls, app, loop):
        for task in app.websocket_tasks:
            task.cancel()

    @staticmethod
    async def _listener(
        app: Sanic, loop: AbstractEventLoop, listener: ListenerType
    ):
        maybe_coro = listener(app, loop)
        if maybe_coro and isawaitable(maybe_coro):
            await maybe_coro

    # -------------------------------------------------------------------- #
    # Task management
    # -------------------------------------------------------------------- #

    @classmethod
    def _prep_task(
        cls,
        task,
        app,
        loop,
    ):
        if callable(task):
            try:
                task = task(app)
            except TypeError:
                task = task()

        return task

    @classmethod
    def _loop_add_task(
        cls,
        task,
        app,
        loop,
        *,
        name: Optional[str] = None,
        register: bool = True,
    ) -> Task:
        if not isinstance(task, Future):
            prepped = cls._prep_task(task, app, loop)
            if sys.version_info < (3, 8):
                if name:
                    error_logger.warning(
                        "Cannot set a name for a task when using Python 3.7. "
                        "Your task will be created without a name."
                    )
                task = loop.create_task(prepped)
            else:
                task = loop.create_task(prepped, name=name)

        if name and register and sys.version_info > (3, 7):
            app._task_registry[name] = task

        return task

    @staticmethod
    async def dispatch_delayed_tasks(app, loop):
        for name in app._delayed_tasks:
            await app.dispatch(name, context={"app": app, "loop": loop})
        app._delayed_tasks.clear()

    @staticmethod
    async def run_delayed_task(app, loop, task):
        prepped = app._prep_task(task, app, loop)
        await prepped

    def add_task(
        self,
        task: Union[Future[Any], Coroutine[Any, Any, Any], Awaitable[Any]],
        *,
        name: Optional[str] = None,
        register: bool = True,
    ) -> Optional[Task]:
        """
        Schedule a task to run later, after the loop has started.
        Different from asyncio.ensure_future in that it does not
        also return a future, and the actual ensure_future call
        is delayed until before server start.

        `See user guide re: background tasks
        <https://sanicframework.org/guide/basics/tasks.html#background-tasks>`__

        :param task: future, couroutine or awaitable
        """
        if name and sys.version_info == (3, 7):
            name = None
            error_logger.warning(
                "Cannot set a name for a task when using Python 3.7. Your "
                "task will be created without a name."
            )
        try:
            loop = self.loop  # Will raise SanicError if loop is not started
            return self._loop_add_task(
                task, self, loop, name=name, register=register
            )
        except SanicException:
            task_name = f"sanic.delayed_task.{hash(task)}"
            if not self._delayed_tasks:
                self.after_server_start(partial(self.dispatch_delayed_tasks))

            if name:
                raise RuntimeError(
                    "Cannot name task outside of a running application"
                )

            self.signal(task_name)(partial(self.run_delayed_task, task=task))
            self._delayed_tasks.append(task_name)
            return None

    def get_task(
        self, name: str, *, raise_exception: bool = True
    ) -> Optional[Task]:
        if sys.version_info < (3, 8):
            error_logger.warning(
                "This feature (get_task) is only supported on using "
                "Python 3.8+."
            )
            return
        try:
            return self._task_registry[name]
        except KeyError:
            if raise_exception:
                raise SanicException(
                    f'Registered task named "{name}" not found.'
                )
            return None

    async def cancel_task(
        self,
        name: str,
        msg: Optional[str] = None,
        *,
        raise_exception: bool = True,
    ) -> None:
        if sys.version_info < (3, 8):
            error_logger.warning(
                "This feature (cancel_task) is only supported on using "
                "Python 3.8+."
            )
            return
        task = self.get_task(name, raise_exception=raise_exception)
        if task and not task.cancelled():
            args: Tuple[str, ...] = ()
            if msg:
                if sys.version_info >= (3, 9):
                    args = (msg,)
                else:
                    raise RuntimeError(
                        "Cancelling a task with a message is only supported "
                        "on Python 3.9+."
                    )
            task.cancel(*args)
            try:
                await task
            except CancelledError:
                ...

    def purge_tasks(self):
        if sys.version_info < (3, 8):
            error_logger.warning(
                "This feature (purge_tasks) is only supported on using "
                "Python 3.8+."
            )
            return
        for task in self.tasks:
            if task.done() or task.cancelled():
                name = task.get_name()
                self._task_registry[name] = None

        self._task_registry = {
            k: v for k, v in self._task_registry.items() if v is not None
        }

    def shutdown_tasks(
        self, timeout: Optional[float] = None, increment: float = 0.1
    ):
        if sys.version_info < (3, 8):
            error_logger.warning(
                "This feature (shutdown_tasks) is only supported on using "
                "Python 3.8+."
            )
            return
        for task in self.tasks:
            task.cancel()

        if timeout is None:
            timeout = self.config.GRACEFUL_SHUTDOWN_TIMEOUT

        while len(self._task_registry) and timeout:
            self.loop.run_until_complete(asyncio.sleep(increment))
            self.purge_tasks()
            timeout -= increment

    @property
    def tasks(self):
        if sys.version_info < (3, 8):
            error_logger.warning(
                "This feature (tasks) is only supported on using "
                "Python 3.8+."
            )
            return
        return iter(self._task_registry.values())

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
        if scope["type"] == "lifespan":
            self.motd("")
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

    @property
    def asgi(self):
        return self.state.asgi

    @asgi.setter
    def asgi(self, value: bool):
        self.state.asgi = value

    @property
    def debug(self):
        return self.state.is_debug

    @debug.setter
    def debug(self, value: bool):
        mode = Mode.DEBUG if value else Mode.PRODUCTION
        self.state.mode = mode

    @property
    def auto_reload(self):
        return self.config.AUTO_RELOAD

    @auto_reload.setter
    def auto_reload(self, value: bool):
        self.config.AUTO_RELOAD = value

    @property
    def state(self):
        return self._state

    @property
    def is_running(self):
        return self.state.is_running

    @is_running.setter
    def is_running(self, value: bool):
        self.state.is_running = value

    @property
    def is_stopping(self):
        return self.state.is_stopping

    @is_stopping.setter
    def is_stopping(self, value: bool):
        self.state.is_stopping = value

    @property
    def reload_dirs(self):
        return self.state.reload_dirs

    def motd(self, serve_location):
        if self.config.MOTD:
            mode = [f"{self.state.mode},"]
            if self.state.fast:
                mode.append("goin' fast")
            if self.state.asgi:
                mode.append("ASGI")
            else:
                if self.state.workers == 1:
                    mode.append("single worker")
                else:
                    mode.append(f"w/ {self.state.workers} workers")

            display = {
                "mode": " ".join(mode),
                "server": self.state.server,
                "python": platform.python_version(),
                "platform": platform.platform(),
            }
            extra = {}
            if self.config.AUTO_RELOAD:
                reload_display = "enabled"
                if self.state.reload_dirs:
                    reload_display += ", ".join(
                        [
                            "",
                            *(
                                str(path.absolute())
                                for path in self.state.reload_dirs
                            ),
                        ]
                    )
                display["auto-reload"] = reload_display

            packages = []
            for package_name in SANIC_PACKAGES:
                module_name = package_name.replace("-", "_")
                try:
                    module = import_module(module_name)
                    packages.append(f"{package_name}=={module.__version__}")
                except ImportError:
                    ...

            if packages:
                display["packages"] = ", ".join(packages)

            if self.config.MOTD_DISPLAY:
                extra.update(self.config.MOTD_DISPLAY)

            logo = (
                get_logo(coffee=self.state.coffee)
                if self.config.LOGO == "" or self.config.LOGO is True
                else self.config.LOGO
            )
            MOTD.output(logo, serve_location, display, extra)

    @property
    def ext(self) -> Extend:
        if not hasattr(self, "_ext"):
            setup_ext(self, fail=True)

        if not hasattr(self, "_ext"):
            raise RuntimeError(
                "Sanic Extensions is not installed. You can add it to your "
                "environment using:\n$ pip install sanic[ext]\nor\n$ pip "
                "install sanic-ext"
            )
        return self._ext  # type: ignore

    def extend(
        self,
        *,
        extensions: Optional[List[Type[Extension]]] = None,
        built_in_extensions: bool = True,
        config: Optional[Union[Config, Dict[str, Any]]] = None,
        **kwargs,
    ) -> Extend:
        if hasattr(self, "_ext"):
            raise RuntimeError(
                "Cannot extend Sanic after Sanic Extensions has been setup."
            )
        setup_ext(
            self,
            extensions=extensions,
            built_in_extensions=built_in_extensions,
            config=config,
            fail=True,
            **kwargs,
        )
        return self.ext

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
    # Lifecycle
    # -------------------------------------------------------------------- #

    def finalize(self):
        try:
            self.router.finalize()
        except FinalizationError as e:
            if not Sanic.test_mode:
                raise e

    def signalize(self):
        try:
            self.signal_router.finalize()
        except FinalizationError as e:
            if not Sanic.test_mode:
                raise e

    async def _startup(self):
        self._future_registry.clear()

        # Startup Sanic Extensions
        if not hasattr(self, "_ext"):
            setup_ext(self)
        if hasattr(self, "_ext"):
            self.ext._display()

        # Setup routers
        self.signalize()
        self.finalize()

        # TODO: Replace in v22.6 to check against apps in app registry
        if (
            self.__class__._uvloop_setting is not None
            and self.__class__._uvloop_setting != self.config.USE_UVLOOP
        ):
            error_logger.warning(
                "It looks like you're running several apps with different "
                "uvloop settings. This is not supported and may lead to "
                "unintended behaviour."
            )
        self.__class__._uvloop_setting = self.config.USE_UVLOOP

        # Startup time optimizations
        ErrorHandler.finalize(self.error_handler, config=self.config)
        TouchUp.run(self)

        self.state.is_started = True

    async def _server_event(
        self,
        concern: str,
        action: str,
        loop: Optional[AbstractEventLoop] = None,
    ) -> None:
        event = f"server.{concern}.{action}"
        if action not in ("before", "after") or concern not in (
            "init",
            "shutdown",
        ):
            raise SanicException(f"Invalid server event: {event}")
        if self.state.verbosity >= 1:
            logger.debug(f"Triggering server events: {event}")
        reverse = concern == "shutdown"
        if loop is None:
            loop = self.loop
        await self.dispatch(
            event,
            fail_not_found=False,
            reverse=reverse,
            inline=True,
            context={
                "app": self,
                "loop": loop,
            },
        )
