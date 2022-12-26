from __future__ import annotations

import asyncio
import logging
import logging.config
import re
import sys

from asyncio import (
    AbstractEventLoop,
    CancelledError,
    Task,
    ensure_future,
    get_running_loop,
    wait_for,
)
from asyncio.futures import Future
from collections import defaultdict, deque
from contextlib import suppress
from functools import partial
from inspect import isawaitable
from os import environ
from socket import socket
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

from sanic_routing.exceptions import FinalizationError, NotFound
from sanic_routing.route import Route

from sanic.application.ext import setup_ext
from sanic.application.state import ApplicationState, ServerStage
from sanic.asgi import ASGIApp
from sanic.base.root import BaseSanic
from sanic.blueprint_group import BlueprintGroup
from sanic.blueprints import Blueprint
from sanic.compat import OS_IS_WINDOWS, enable_windows_color_support
from sanic.config import SANIC_PREFIX, Config
from sanic.exceptions import (
    BadRequest,
    SanicException,
    ServerError,
    URLBuildError,
)
from sanic.handlers import ErrorHandler
from sanic.helpers import Default, _default
from sanic.http import Stage
from sanic.log import (
    LOGGING_CONFIG_DEFAULTS,
    deprecation,
    error_logger,
    logger,
)
from sanic.middleware import Middleware, MiddlewareLocation
from sanic.mixins.listeners import ListenerEvent
from sanic.mixins.startup import StartupMixin
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
from sanic.server.websockets.impl import ConnectionClosed
from sanic.signals import Signal, SignalRouter
from sanic.touchup import TouchUp, TouchUpMeta
from sanic.types.shared_ctx import SharedContext
from sanic.worker.inspector import Inspector
from sanic.worker.manager import WorkerManager


if TYPE_CHECKING:
    try:
        from sanic_ext import Extend  # type: ignore
        from sanic_ext.extensions.base import Extension  # type: ignore
    except ImportError:
        Extend = TypeVar("Extend", Type)  # type: ignore


if OS_IS_WINDOWS:  # no cov
    enable_windows_color_support()


class Sanic(BaseSanic, StartupMixin, metaclass=TouchUpMeta):
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
        "_inspector",
        "_manager",
        "_state",
        "_task_registry",
        "_test_client",
        "_test_manager",
        "blueprints",
        "config",
        "configure_logging",
        "ctx",
        "error_handler",
        "inspector_class",
        "go_fast",
        "listeners",
        "multiplexer",
        "named_request_middleware",
        "named_response_middleware",
        "request_class",
        "request_middleware",
        "response_middleware",
        "router",
        "shared_ctx",
        "signal_router",
        "sock",
        "strict_slashes",
        "websocket_enabled",
        "websocket_tasks",
    )

    _app_registry: Dict[str, "Sanic"] = {}
    test_mode = False

    def __init__(
        self,
        name: Optional[str] = None,
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
        dumps: Optional[Callable[..., AnyStr]] = None,
        loads: Optional[Callable[..., Any]] = None,
        inspector: bool = False,
        inspector_class: Optional[Type[Inspector]] = None,
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
        if inspector:
            self.config.INSPECTOR = inspector

        # Then we can do the rest
        self._asgi_client: Any = None
        self._blueprint_order: List[Blueprint] = []
        self._delayed_tasks: List[str] = []
        self._future_registry: FutureRegistry = FutureRegistry()
        self._inspector: Optional[Inspector] = None
        self._manager: Optional[WorkerManager] = None
        self._state: ApplicationState = ApplicationState(app=self)
        self._task_registry: Dict[str, Task] = {}
        self._test_client: Any = None
        self._test_manager: Any = None
        self.asgi = False
        self.auto_reload = False
        self.blueprints: Dict[str, Blueprint] = {}
        self.configure_logging: bool = configure_logging
        self.ctx: Any = ctx or SimpleNamespace()
        self.error_handler: ErrorHandler = error_handler or ErrorHandler()
        self.inspector_class: Type[Inspector] = inspector_class or Inspector
        self.listeners: Dict[str, List[ListenerType[Any]]] = defaultdict(list)
        self.named_request_middleware: Dict[str, Deque[MiddlewareType]] = {}
        self.named_response_middleware: Dict[str, Deque[MiddlewareType]] = {}
        self.request_class: Type[Request] = request_class or Request
        self.request_middleware: Deque[MiddlewareType] = deque()
        self.response_middleware: Deque[MiddlewareType] = deque()
        self.router: Router = router or Router()
        self.shared_ctx: SharedContext = SharedContext()
        self.signal_router: SignalRouter = signal_router or SignalRouter()
        self.sock: Optional[socket] = None
        self.strict_slashes: bool = strict_slashes
        self.websocket_enabled: bool = False
        self.websocket_tasks: Set[Future[Any]] = set()

        # Register alternative method names
        self.go_fast = self.run
        self.router.ctx.app = self
        self.signal_router.ctx.app = self
        self.__class__.register_app(self)

        if dumps:
            BaseHTTPResponse._dumps = dumps  # type: ignore
        if loads:
            Request._loads = loads  # type: ignore

    @property
    def loop(self):
        """
        Synonymous with asyncio.get_event_loop().

        .. note::

            Only supported when using the `app.run` method.
        """
        if self.state.stage is ServerStage.STOPPED and self.asgi is False:
            raise SanicException(
                "Loop can only be retrieved after the app has started "
                "running. Not supported with `create_server` function"
            )
        try:
            return get_running_loop()
        except RuntimeError:  # no cov
            if sys.version_info > (3, 10):
                return asyncio.get_event_loop_policy().get_event_loop()
            else:
                return asyncio.get_event_loop()

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
            raise BadRequest(f"Invalid event: {event}. Use one of: {valid}")

        if "." in _event:
            self.signal(_event.value)(
                partial(self._listener, listener=listener)
            )
        else:
            self.listeners[_event.value].append(listener)

        return listener

    def register_middleware(
        self,
        middleware: Union[MiddlewareType, Middleware],
        attach_to: str = "request",
        *,
        priority: Union[Default, int] = _default,
    ) -> Union[MiddlewareType, Middleware]:
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
        retval = middleware
        location = MiddlewareLocation[attach_to.upper()]

        if not isinstance(middleware, Middleware):
            middleware = Middleware(
                middleware,
                location=location,
                priority=priority if isinstance(priority, int) else 0,
            )
        elif middleware.priority != priority and isinstance(priority, int):
            middleware = Middleware(
                middleware.func,
                location=middleware.location,
                priority=priority,
            )

        if location is MiddlewareLocation.REQUEST:
            if middleware not in self.request_middleware:
                self.request_middleware.append(middleware)
        if location is MiddlewareLocation.RESPONSE:
            if middleware not in self.response_middleware:
                self.response_middleware.appendleft(middleware)
        return retval

    def register_named_middleware(
        self,
        middleware: MiddlewareType,
        route_names: Iterable[str],
        attach_to: str = "request",
        *,
        priority: Union[Default, int] = _default,
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
        retval = middleware
        location = MiddlewareLocation[attach_to.upper()]

        if not isinstance(middleware, Middleware):
            middleware = Middleware(
                middleware,
                location=location,
                priority=priority if isinstance(priority, int) else 0,
            )
        elif middleware.priority != priority and isinstance(priority, int):
            middleware = Middleware(
                middleware.func,
                location=middleware.location,
                priority=priority,
            )

        if location is MiddlewareLocation.REQUEST:
            for _rn in route_names:
                if _rn not in self.named_request_middleware:
                    self.named_request_middleware[_rn] = deque()
                if middleware not in self.named_request_middleware[_rn]:
                    self.named_request_middleware[_rn].append(middleware)
        if location is MiddlewareLocation.RESPONSE:
            for _rn in route_names:
                if _rn not in self.named_response_middleware:
                    self.named_response_middleware[_rn] = deque()
                if middleware not in self.named_response_middleware[_rn]:
                    self.named_response_middleware[_rn].appendleft(middleware)
        return retval

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
            r.extra.websocket = websocket
            r.extra.static = params.get("static", False)
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
        blueprint: Union[Blueprint, Iterable[Blueprint], BlueprintGroup],
        **options: Any,
    ):
        """Register a blueprint on the application.

        :param blueprint: Blueprint object or (list, tuple) thereof
        :param options: option dictionary with blueprint defaults
        :return: Nothing
        """
        if isinstance(blueprint, (Iterable, BlueprintGroup)):
            for item in blueprint:
                params = {**options}
                if isinstance(blueprint, BlueprintGroup):
                    merge_from = [
                        options.get("url_prefix", ""),
                        blueprint.url_prefix or "",
                    ]
                    if not isinstance(item, BlueprintGroup):
                        merge_from.append(item.url_prefix or "")
                    merged_prefix = "/".join(
                        u.strip("/") for u in merge_from if u
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

        if getattr(route.extra, "static", None):
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
        if route.extra.hosts and external:
            if not host and len(route.extra.hosts) > 1:
                raise ValueError(
                    f"Host is ambiguous: {', '.join(route.extra.hosts)}"
                )
            elif host and host not in route.extra.hosts:
                raise ValueError(
                    f"Requested host ({host}) is not available for this "
                    f"route: {route.extra.hosts}"
                )
            elif not host:
                host = list(route.extra.hosts)[0]

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
        self,
        request: Request,
        exception: BaseException,
        run_middleware: bool = True,
    ):  # no cov
        """
        A handler that catches specific exceptions and outputs a response.

        :param request: The current request object
        :param exception: The exception that was raised
        :raises ServerError: response 500
        """
        response = None
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

            handler = self.error_handler._lookup(
                exception, request.name if request else None
            )
            if handler:
                logger.warning(
                    "An error occurred while handling the request after at "
                    "least some part of the response was sent to the client. "
                    "The response from your custom exception handler "
                    f"{handler.__name__} will not be sent to the client."
                    "Exception handlers should only be used to generate the "
                    "exception responses. If you would like to perform any "
                    "other action on a raised exception, consider using a "
                    "signal handler like "
                    '`@app.signal("http.lifecycle.exception")`\n'
                    "For further information, please see the docs: "
                    "https://sanicframework.org/en/guide/advanced/"
                    "signals.html",
                )
            return

        # -------------------------------------------- #
        # Request Middleware
        # -------------------------------------------- #
        if run_middleware:
            middleware = (
                request.route and request.route.extra.request_middleware
            ) or self.request_middleware
            response = await self._run_request_middleware(request, middleware)
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
        response: Optional[
            Union[
                BaseHTTPResponse,
                Coroutine[Any, Any, Optional[BaseHTTPResponse]],
            ]
        ] = None
        run_middleware = True
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
                and not route.extra.ignore_body
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
            run_middleware = False
            if request.route.extra.request_middleware:
                response = await self._run_request_middleware(
                    request, request.route.extra.request_middleware
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
                await self.dispatch(
                    "http.handler.before",
                    inline=True,
                    context={"request": request},
                )
                response = handler(request, **request.match_info)
                if isawaitable(response):
                    response = await response
                await self.dispatch(
                    "http.handler.after",
                    inline=True,
                    context={"request": request},
                )

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
                response = await request.respond(response)  # type: ignore
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
                ...
                await response.send(end_stream=True)
            elif isinstance(response, ResponseStream):
                resp = await response(request)  # type: ignore
                await self.dispatch(
                    "http.lifecycle.response",
                    inline=True,
                    context={
                        "request": request,
                        "response": resp,
                    },
                )
                await response.eof()  # type: ignore
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
            await self.handle_exception(
                request, e, run_middleware=run_middleware
            )

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
        except (CancelledError, ConnectionClosed):
            cancelled = True
        except Exception as e:
            self.error_handler.log(request, e)
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
        execute handlers.

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

    async def _run_request_middleware(
        self, request, middleware_collection
    ):  # no cov
        request._request_middleware_started = True

        for middleware in middleware_collection:
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
        self, request, response, middleware_collection
    ):  # no cov
        for middleware in middleware_collection:
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
        try:
            maybe_coro = listener(app)  # type: ignore
        except TypeError:
            maybe_coro = listener(app, loop)  # type: ignore
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
            if sys.version_info < (3, 8):  # no cov
                task = loop.create_task(prepped)
                if name:
                    error_logger.warning(
                        "Cannot set a name for a task when using Python 3.7. "
                        "Your task will be created without a name."
                    )
                task.get_name = lambda: name
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
    ) -> Optional[Task[Any]]:
        """
        Schedule a task to run later, after the loop has started.
        Different from asyncio.ensure_future in that it does not
        also return a future, and the actual ensure_future call
        is delayed until before server start.

        `See user guide re: background tasks
        <https://sanicframework.org/guide/basics/tasks.html#background-tasks>`__

        :param task: future, coroutine or awaitable
        """
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
        task = self.get_task(name, raise_exception=raise_exception)
        if task and not task.cancelled():
            args: Tuple[str, ...] = ()
            if msg:
                if sys.version_info >= (3, 9):
                    args = (msg,)
                else:  # no cov
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
        for key, task in self._task_registry.items():
            if task.done() or task.cancelled():
                self._task_registry[key] = None

        self._task_registry = {
            k: v for k, v in self._task_registry.items() if v is not None
        }

    def shutdown_tasks(
        self, timeout: Optional[float] = None, increment: float = 0.1
    ):
        for task in self.tasks:
            if task.get_name() != "RunServer":
                task.cancel()

        if timeout is None:
            timeout = self.config.GRACEFUL_SHUTDOWN_TIMEOUT

        while len(self._task_registry) and timeout:
            with suppress(RuntimeError):
                running_loop = get_running_loop()
                running_loop.run_until_complete(asyncio.sleep(increment))
            self.purge_tasks()
            timeout -= increment

    @property
    def tasks(self):
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
    def asgi(self) -> bool:
        return self.state.asgi

    @asgi.setter
    def asgi(self, value: bool):
        self.state.asgi = value

    @property
    def debug(self):
        return self.state.is_debug

    @property
    def auto_reload(self):
        return self.config.AUTO_RELOAD

    @auto_reload.setter
    def auto_reload(self, value: bool):
        self.config.AUTO_RELOAD = value
        self.state.auto_reload = value

    @property
    def state(self) -> ApplicationState:  # type: ignore
        """
        :return: The application state
        """
        return self._state

    @property
    def reload_dirs(self):
        return self.state.reload_dirs

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
    def unregister_app(cls, app: "Sanic") -> None:
        """
        Unregister a Sanic instance
        """
        if not isinstance(app, cls):
            raise SanicException("Registered app must be an instance of Sanic")

        name = app.name
        if name in cls._app_registry:
            del cls._app_registry[name]

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
            if name == "__main__":
                return cls.get_app("__mp_main__", force_create=force_create)
            if force_create:
                return cls(name)
            raise SanicException(
                f"Sanic app name '{name}' not found.\n"
                "App instantiation must occur outside "
                "if __name__ == '__main__' "
                "block or by using an AppLoader.\nSee "
                "https://sanic.dev/en/guide/deployment/app-loader.html"
                " for more details."
            )

    @classmethod
    def _check_uvloop_conflict(cls) -> None:
        values = {app.config.USE_UVLOOP for app in cls._app_registry.values()}
        if len(values) > 1:
            error_logger.warning(
                "It looks like you're running several apps with different "
                "uvloop settings. This is not supported and may lead to "
                "unintended behaviour."
            )

    # -------------------------------------------------------------------- #
    # Lifecycle
    # -------------------------------------------------------------------- #

    def finalize(self):
        try:
            self.router.finalize()
        except FinalizationError as e:
            if not Sanic.test_mode:
                raise e
        self.finalize_middleware()

    def signalize(self, allow_fail_builtin=True):
        self.signal_router.allow_fail_builtin = allow_fail_builtin
        try:
            self.signal_router.finalize()
        except FinalizationError as e:
            if not Sanic.test_mode:
                raise e

    async def _startup(self):
        self._future_registry.clear()

        if not hasattr(self, "_ext"):
            setup_ext(self)
        if hasattr(self, "_ext"):
            self.ext._display()

        if self.state.is_debug and self.config.TOUCHUP is not True:
            self.config.TOUCHUP = False
        elif isinstance(self.config.TOUCHUP, Default):
            self.config.TOUCHUP = True

        # Setup routers
        self.signalize(self.config.TOUCHUP)
        self.finalize()

        route_names = [route.name for route in self.router.routes]
        duplicates = {
            name for name in route_names if route_names.count(name) > 1
        }
        if duplicates:
            names = ", ".join(duplicates)
            deprecation(
                f"Duplicate route names detected: {names}. In the future, "
                "Sanic will enforce uniqueness in route naming.",
                23.3,
            )

        Sanic._check_uvloop_conflict()

        # Startup time optimizations
        if self.state.primary:
            # TODO:
            # - Raise warning if secondary apps have error handler config
            if self.config.TOUCHUP:
                TouchUp.run(self)

        self.state.is_started = True

    def ack(self):
        if hasattr(self, "multiplexer"):
            self.multiplexer.ack()

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
        logger.debug(
            f"Triggering server events: {event}", extra={"verbosity": 1}
        )
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

    # -------------------------------------------------------------------- #
    # Process Management
    # -------------------------------------------------------------------- #

    def refresh(
        self,
        passthru: Optional[Dict[str, Any]] = None,
    ):
        registered = self.__class__.get_app(self.name)
        if self is not registered:
            if not registered.state.server_info:
                registered.state.server_info = self.state.server_info
            self = registered
        if passthru:
            for attr, info in passthru.items():
                if isinstance(info, dict):
                    for key, value in info.items():
                        setattr(getattr(self, attr), key, value)
                else:
                    setattr(self, attr, info)
        if hasattr(self, "multiplexer"):
            self.shared_ctx.lock()
        return self

    @property
    def inspector(self):
        if environ.get("SANIC_WORKER_PROCESS") or not self._inspector:
            raise SanicException(
                "Can only access the inspector from the main process"
            )
        return self._inspector

    @property
    def manager(self):
        if environ.get("SANIC_WORKER_PROCESS") or not self._manager:
            raise SanicException(
                "Can only access the manager from the main process"
            )
        return self._manager
