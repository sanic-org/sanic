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
from collections.abc import Awaitable, Coroutine, Iterable, Iterator
from contextlib import contextmanager, suppress
from enum import Enum
from functools import partial, wraps
from inspect import isawaitable
from os import environ
from pathlib import Path
from socket import socket
from traceback import format_exc
from types import SimpleNamespace
from typing import (
    TYPE_CHECKING,
    Any,
    AnyStr,
    Callable,
    ClassVar,
    Deque,
    Generic,
    Literal,
    Optional,
    TypeVar,
    Union,
    cast,
    overload,
)
from urllib.parse import urlencode, urlunparse

from sanic_routing.exceptions import FinalizationError, NotFound
from sanic_routing.route import Route

from sanic.application.ext import setup_ext
from sanic.application.state import ApplicationState, ServerStage
from sanic.asgi import ASGIApp, Lifespan
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
from sanic.log import LOGGING_CONFIG_DEFAULTS, error_logger, logger
from sanic.logging.setup import setup_logging
from sanic.middleware import Middleware, MiddlewareLocation
from sanic.mixins.commands import CommandMixin
from sanic.mixins.listeners import ListenerEvent
from sanic.mixins.startup import StartupMixin
from sanic.mixins.static import StaticHandleMixin
from sanic.models.ctx_types import REPLContext
from sanic.models.futures import (
    FutureException,
    FutureListener,
    FutureMiddleware,
    FutureRegistry,
    FutureRoute,
    FutureSignal,
)
from sanic.models.handler_types import ListenerType, MiddlewareType
from sanic.models.handler_types import Sanic as SanicVar
from sanic.request import Request
from sanic.response import BaseHTTPResponse, HTTPResponse, ResponseStream
from sanic.router import Router
from sanic.server.websockets.impl import ConnectionClosed
from sanic.signals import Event, Signal, SignalRouter
from sanic.touchup import TouchUp, TouchUpMeta
from sanic.types.shared_ctx import SharedContext
from sanic.worker.inspector import Inspector
from sanic.worker.loader import CertLoader
from sanic.worker.manager import WorkerManager


if TYPE_CHECKING:
    try:
        from sanic_ext import Extend  # type: ignore
        from sanic_ext.extensions.base import Extension  # type: ignore
    except ImportError:
        Extend = TypeVar("Extend", type)  # type: ignore


if OS_IS_WINDOWS:  # no cov
    enable_windows_color_support()

ctx_type = TypeVar("ctx_type")
config_type = TypeVar("config_type", bound=Config)


class Sanic(
    Generic[config_type, ctx_type],
    StaticHandleMixin,
    BaseSanic,
    StartupMixin,
    CommandMixin,
    metaclass=TouchUpMeta,
):
    """The main application instance

    You will create an instance of this class and use it to register
    routes, listeners, middleware, blueprints, error handlers, etc.

    By convention, it is often called `app`. It must be named using
    the `name` parameter and is roughly constrained to the same
    restrictions as a Python module name, however, it can contain
    hyphens (`-`).

    ```python
    # will cause an error because it contains spaces
    Sanic("This is not legal")
    ```

    ```python
    # this is legal
    Sanic("Hyphens-are-legal_or_also_underscores")
    ```

    Args:
        name (str): The name of the application. Must be a valid
            Python module name (including hyphens).
        config (Optional[config_type]): The configuration to use for
            the application. Defaults to `None`.
        ctx (Optional[ctx_type]): The context to use for the
            application. Defaults to `None`.
        router (Optional[Router]): The router to use for the
            application. Defaults to `None`.
        signal_router (Optional[SignalRouter]): The signal router to
            use for the application. Defaults to `None`.
        error_handler (Optional[ErrorHandler]): The error handler to
            use for the application. Defaults to `None`.
        env_prefix (Optional[str]): The prefix to use for environment
            variables. Defaults to `SANIC_`.
        request_class (Optional[Type[Request]]): The request class to
            use for the application. Defaults to `Request`.
        strict_slashes (bool): Whether to enforce strict slashes.
            Defaults to `False`.
        log_config (Optional[Dict[str, Any]]): The logging configuration
            to use for the application. Defaults to `None`.
        configure_logging (bool): Whether to configure logging.
            Defaults to `True`.
        dumps (Optional[Callable[..., AnyStr]]): The function to use
            for serializing JSON. Defaults to `None`.
        loads (Optional[Callable[..., Any]]): The function to use
            for deserializing JSON. Defaults to `None`.
        inspector (bool): Whether to enable the inspector. Defaults
            to `False`.
        inspector_class (Optional[Type[Inspector]]): The inspector
            class to use for the application. Defaults to `None`.
        certloader_class (Optional[Type[CertLoader]]): The certloader
            class to use for the application. Defaults to `None`.
    """

    __touchup__ = (
        "handle_request",
        "handle_exception",
        "_run_response_middleware",
        "_run_request_middleware",
    )
    __slots__ = (
        "_asgi_app",
        "_asgi_lifespan",
        "_asgi_client",
        "_blueprint_order",
        "_delayed_tasks",
        "_ext",
        "_future_commands",
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
        "certloader_class",
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
        "repl_ctx",
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

    _app_registry: ClassVar[dict[str, Sanic]] = {}
    test_mode: ClassVar[bool] = False

    @overload
    def __init__(
        self: Sanic[Config, SimpleNamespace],
        name: str,
        config: None = None,
        ctx: None = None,
        router: Optional[Router] = None,
        signal_router: Optional[SignalRouter] = None,
        error_handler: Optional[ErrorHandler] = None,
        env_prefix: Optional[str] = SANIC_PREFIX,
        request_class: Optional[type[Request]] = None,
        strict_slashes: bool = False,
        log_config: Optional[dict[str, Any]] = None,
        configure_logging: bool = True,
        dumps: Optional[Callable[..., AnyStr]] = None,
        loads: Optional[Callable[..., Any]] = None,
        inspector: bool = False,
        inspector_class: Optional[type[Inspector]] = None,
        certloader_class: Optional[type[CertLoader]] = None,
    ) -> None: ...

    @overload
    def __init__(
        self: Sanic[config_type, SimpleNamespace],
        name: str,
        config: Optional[config_type] = None,
        ctx: None = None,
        router: Optional[Router] = None,
        signal_router: Optional[SignalRouter] = None,
        error_handler: Optional[ErrorHandler] = None,
        env_prefix: Optional[str] = SANIC_PREFIX,
        request_class: Optional[type[Request]] = None,
        strict_slashes: bool = False,
        log_config: Optional[dict[str, Any]] = None,
        configure_logging: bool = True,
        dumps: Optional[Callable[..., AnyStr]] = None,
        loads: Optional[Callable[..., Any]] = None,
        inspector: bool = False,
        inspector_class: Optional[type[Inspector]] = None,
        certloader_class: Optional[type[CertLoader]] = None,
    ) -> None: ...

    @overload
    def __init__(
        self: Sanic[Config, ctx_type],
        name: str,
        config: None = None,
        ctx: Optional[ctx_type] = None,
        router: Optional[Router] = None,
        signal_router: Optional[SignalRouter] = None,
        error_handler: Optional[ErrorHandler] = None,
        env_prefix: Optional[str] = SANIC_PREFIX,
        request_class: Optional[type[Request]] = None,
        strict_slashes: bool = False,
        log_config: Optional[dict[str, Any]] = None,
        configure_logging: bool = True,
        dumps: Optional[Callable[..., AnyStr]] = None,
        loads: Optional[Callable[..., Any]] = None,
        inspector: bool = False,
        inspector_class: Optional[type[Inspector]] = None,
        certloader_class: Optional[type[CertLoader]] = None,
    ) -> None: ...

    @overload
    def __init__(
        self: Sanic[config_type, ctx_type],
        name: str,
        config: Optional[config_type] = None,
        ctx: Optional[ctx_type] = None,
        router: Optional[Router] = None,
        signal_router: Optional[SignalRouter] = None,
        error_handler: Optional[ErrorHandler] = None,
        env_prefix: Optional[str] = SANIC_PREFIX,
        request_class: Optional[type[Request]] = None,
        strict_slashes: bool = False,
        log_config: Optional[dict[str, Any]] = None,
        configure_logging: bool = True,
        dumps: Optional[Callable[..., AnyStr]] = None,
        loads: Optional[Callable[..., Any]] = None,
        inspector: bool = False,
        inspector_class: Optional[type[Inspector]] = None,
        certloader_class: Optional[type[CertLoader]] = None,
    ) -> None: ...

    def __init__(
        self,
        name: str,
        config: Optional[config_type] = None,
        ctx: Optional[ctx_type] = None,
        router: Optional[Router] = None,
        signal_router: Optional[SignalRouter] = None,
        error_handler: Optional[ErrorHandler] = None,
        env_prefix: Optional[str] = SANIC_PREFIX,
        request_class: Optional[type[Request]] = None,
        strict_slashes: bool = False,
        log_config: Optional[dict[str, Any]] = None,
        configure_logging: bool = True,
        dumps: Optional[Callable[..., AnyStr]] = None,
        loads: Optional[Callable[..., Any]] = None,
        inspector: bool = False,
        inspector_class: Optional[type[Inspector]] = None,
        certloader_class: Optional[type[CertLoader]] = None,
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
        self.config: config_type = cast(
            config_type, config or Config(env_prefix=env_prefix)
        )
        if inspector:
            self.config.INSPECTOR = inspector

        # Then we can do the rest
        self._asgi_app: Optional[ASGIApp] = None
        self._asgi_lifespan: Optional[Lifespan] = None
        self._asgi_client: Any = None
        self._blueprint_order: list[Blueprint] = []
        self._delayed_tasks: list[str] = []
        self._future_registry: FutureRegistry = FutureRegistry()
        self._inspector: Optional[Inspector] = None
        self._manager: Optional[WorkerManager] = None
        self._state: ApplicationState = ApplicationState(app=self)
        self._task_registry: dict[str, Union[Task, None]] = {}
        self._test_client: Any = None
        self._test_manager: Any = None
        self.asgi = False
        self.auto_reload = False
        self.blueprints: dict[str, Blueprint] = {}
        self.certloader_class: type[CertLoader] = (
            certloader_class or CertLoader
        )
        self.configure_logging: bool = configure_logging
        self.ctx: ctx_type = cast(ctx_type, ctx or SimpleNamespace())
        self.error_handler: ErrorHandler = error_handler or ErrorHandler()
        self.inspector_class: type[Inspector] = inspector_class or Inspector
        self.listeners: dict[str, list[ListenerType[Any]]] = defaultdict(list)
        self.named_request_middleware: dict[str, Deque[Middleware]] = {}
        self.named_response_middleware: dict[str, Deque[Middleware]] = {}
        self.repl_ctx: REPLContext = REPLContext()
        self.request_class = request_class or Request
        self.request_middleware: Deque[Middleware] = deque()
        self.response_middleware: Deque[Middleware] = deque()
        self.router: Router = router or Router()
        self.shared_ctx: SharedContext = SharedContext()
        self.signal_router: SignalRouter = signal_router or SignalRouter()
        self.sock: Optional[socket] = None
        self.strict_slashes: bool = strict_slashes
        self.websocket_enabled: bool = False
        self.websocket_tasks: set[Future[Any]] = set()

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
    def loop(self) -> AbstractEventLoop:
        """Synonymous with asyncio.get_event_loop().

        .. note::
            Only supported when using the `app.run` method.

        Returns:
            AbstractEventLoop: The event loop for the application.

        Raises:
            SanicException: If the application is not running.
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
        self,
        listener: ListenerType[SanicVar],
        event: str,
        *,
        priority: int = 0,
    ) -> ListenerType[SanicVar]:
        """Register the listener for a given event.

        Args:
            listener (Callable): The listener to register.
            event (str): The event to listen for.

        Returns:
            Callable: The listener that was registered.
        """

        try:
            _event = ListenerEvent[event.upper()]
        except (ValueError, AttributeError):
            valid = ", ".join(
                map(lambda x: x.lower(), ListenerEvent.__members__.keys())
            )
            raise BadRequest(f"Invalid event: {event}. Use one of: {valid}")

        if "." in _event:
            self.signal(_event.value, priority=priority)(
                partial(self._listener, listener=listener)
            )
        else:
            if priority:
                error_logger.warning(
                    f"Priority is not supported for {_event.value}"
                )
            self.listeners[_event.value].append(listener)

        return listener

    def register_middleware(
        self,
        middleware: Union[MiddlewareType, Middleware],
        attach_to: str = "request",
        *,
        priority: Union[Default, int] = _default,
    ) -> Union[MiddlewareType, Middleware]:
        """Register a middleware to be called before a request is handled.

        Args:
            middleware (Callable): A callable that takes in a request.
            attach_to (str): Whether to attach to request or response.
                Defaults to `'request'`.
            priority (int): The priority level of the middleware.
                Lower numbers are executed first. Defaults to `0`.

        Returns:
            Union[Callable, Callable[[Callable], Callable]]: The decorated
                middleware function or a partial function depending on how
                the method was called.
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
        """Used to register named middleqare (middleware typically on blueprints)

        Args:
            middleware (Callable): A callable that takes in a request.
            route_names (Iterable[str]): The route names to attach the
                middleware to.
            attach_to (str): Whether to attach to request or response.
                Defaults to `'request'`.
            priority (int): The priority level of the middleware.
                Lower numbers are executed first. Defaults to `0`.

        Returns:
            Union[Callable, Callable[[Callable], Callable]]: The decorated
                middleware function or a partial function depending on how
                the method was called.
        """  # noqa: E501
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
        route_names: Optional[list[str]] = None,
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
        return self.register_listener(
            listener.listener, listener.event, priority=listener.priority
        )

    def _apply_route(
        self, route: FutureRoute, overwrite: bool = False
    ) -> list[Route]:
        params = route._asdict()
        params["overwrite"] = overwrite
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

        with self.amend():
            routes = self.router.add(**params)
            if isinstance(routes, Route):
                routes = [routes]

            for r in routes:
                r.extra.websocket = websocket
                r.extra.static = params.get("static", False)
                r.ctx.__dict__.update(ctx)

        return routes

    def _apply_middleware(
        self,
        middleware: FutureMiddleware,
        route_names: Optional[list[str]] = None,
    ):
        with self.amend():
            if route_names:
                return self.register_named_middleware(
                    middleware.middleware, route_names, middleware.attach_to
                )
            else:
                return self.register_middleware(
                    middleware.middleware, middleware.attach_to
                )

    def _apply_signal(self, signal: FutureSignal) -> Signal:
        with self.amend():
            return self.signal_router.add(
                handler=signal.handler,
                event=signal.event,
                condition=signal.condition,
                exclusive=signal.exclusive,
                priority=signal.priority,
            )

    @overload
    def dispatch(
        self,
        event: str,
        *,
        condition: Optional[dict[str, str]] = None,
        context: Optional[dict[str, Any]] = None,
        fail_not_found: bool = True,
        inline: Literal[True],
        reverse: bool = False,
    ) -> Coroutine[Any, Any, Awaitable[Any]]: ...

    @overload
    def dispatch(
        self,
        event: str,
        *,
        condition: Optional[dict[str, str]] = None,
        context: Optional[dict[str, Any]] = None,
        fail_not_found: bool = True,
        inline: Literal[False] = False,
        reverse: bool = False,
    ) -> Coroutine[Any, Any, Awaitable[Task]]: ...

    def dispatch(
        self,
        event: str,
        *,
        condition: Optional[dict[str, str]] = None,
        context: Optional[dict[str, Any]] = None,
        fail_not_found: bool = True,
        inline: bool = False,
        reverse: bool = False,
    ) -> Coroutine[Any, Any, Awaitable[Union[Task, Any]]]:
        """Dispatches an event to the signal router.

        Args:
            event (str): Name of the event to dispatch.
            condition (Optional[Dict[str, str]]): Condition for the
                event dispatch.
            context (Optional[Dict[str, Any]]): Context for the event dispatch.
            fail_not_found (bool): Whether to fail if the event is not found.
                Default is `True`.
            inline (bool): If `True`, returns the result directly. If `False`,
                returns a `Task`. Default is `False`.
            reverse (bool): Whether to reverse the dispatch order.
                Default is `False`.

        Returns:
            Coroutine[Any, Any, Awaitable[Union[Task, Any]]]: An awaitable
                that returns the result directly if `inline=True`, or a `Task`
                if `inline=False`.

        Examples:
            ```python
            @app.signal("user.registration.created")
            async def send_registration_email(**context):
                await send_email(context["email"], template="registration")

            @app.post("/register")
            async def handle_registration(request):
                await do_registration(request)
                await request.app.dispatch(
                    "user.registration.created",
                    context={"email": request.json.email}
                })
            ```
        """
        return self.signal_router.dispatch(
            event,
            context=context,
            condition=condition,
            inline=inline,
            reverse=reverse,
            fail_not_found=fail_not_found,
        )

    async def event(
        self,
        event: Union[str, Enum],
        timeout: Optional[Union[int, float]] = None,
        *,
        condition: Optional[dict[str, Any]] = None,
        exclusive: bool = True,
    ) -> None:
        """Wait for a specific event to be triggered.

        This method waits for a named event to be triggered and can be used
        in conjunction with the signal system to wait for specific signals.
        If the event is not found and auto-registration of events is enabled,
        the event will be registered and then waited on. If the event is not
        found and auto-registration is not enabled, a `NotFound` exception
        is raised.

        Auto-registration can be handled by setting the `EVENT_AUTOREGISTER`
        config value to `True`.

        ```python
        app.config.EVENT_AUTOREGISTER = True
        ```

        Args:
            event (str): The name of the event to wait for.
            timeout (Optional[Union[int, float]]): An optional timeout value
                in seconds. If provided, the wait will be terminated if the
                timeout is reached. Defaults to `None`, meaning no timeout.
            condition: If provided, method will only return when the signal
                is dispatched with the given condition.
            exclusive: When true (default), the signal can only be dispatched
                when the condition has been met. When ``False``, the signal can
                be dispatched either with or without it.

        Raises:
            NotFound: If the event is not found and auto-registration of
                events is not enabled.

        Returns:
            The context dict of the dispatched signal.

        Examples:
            ```python
            async def wait_for_event(app):
                while True:
                    print("> waiting")
                    await app.event("foo.bar.baz")
                    print("> event found")

            @app.after_server_start
            async def after_server_start(app, loop):
                app.add_task(wait_for_event(app))
            ```
        """

        waiter = self.signal_router.get_waiter(event, condition, exclusive)

        if not waiter and self.config.EVENT_AUTOREGISTER:
            self.signal_router.reset()
            self.add_signal(None, event)
            waiter = self.signal_router.get_waiter(event, condition, exclusive)
            self.signal_router.finalize()

        if not waiter:
            raise NotFound(f"Could not find signal {event}")

        return await wait_for(waiter.wait(), timeout=timeout)

    def report_exception(
        self, handler: Callable[[Sanic, Exception], Coroutine[Any, Any, None]]
    ) -> Callable[[Exception], Coroutine[Any, Any, None]]:
        """Register a handler to report exceptions.

        A convenience method to register a handler for the signal that
        is emitted when an exception occurs. It is typically used to
        report exceptions to an external service.

        It is equivalent to:

        ```python
        @app.signal(Event.SERVER_EXCEPTION_REPORT)
        async def report(exception):
            await do_something_with_error(exception)
        ```

        Args:
            handler (Callable[[Sanic, Exception], Coroutine[Any, Any, None]]):
                The handler to register.

        Returns:
            Callable[[Sanic, Exception], Coroutine[Any, Any, None]]: The
                handler that was registered.
        """

        @wraps(handler)
        async def report(exception: Exception) -> None:
            await handler(self, exception)

        self.add_signal(
            handler=report, event=Event.SERVER_EXCEPTION_REPORT.value
        )

        return report

    def enable_websocket(self, enable: bool = True) -> None:
        """Enable or disable the support for websocket.

        Websocket is enabled automatically if websocket routes are
        added to the application. This typically will not need to be
        called manually.

        Args:
            enable (bool, optional): If set to `True`, enables websocket
                support. If set to `False`, disables websocket support.
                Defaults to `True`.

        Returns:
            None
        """

        if not self.websocket_enabled:
            # if the server is stopped, we want to cancel any ongoing
            # websocket tasks, to allow the server to exit promptly
            self.listener("before_server_stop")(self._cancel_websocket_tasks)

        self.websocket_enabled = enable

    def blueprint(
        self,
        blueprint: Union[Blueprint, Iterable[Blueprint], BlueprintGroup],
        *,
        url_prefix: Optional[str] = None,
        version: Optional[Union[int, float, str]] = None,
        strict_slashes: Optional[bool] = None,
        version_prefix: Optional[str] = None,
        name_prefix: Optional[str] = None,
    ) -> None:
        """Register a blueprint on the application.

        See [Blueprints](/en/guide/best-practices/blueprints) for more information.

        Args:
            blueprint (Union[Blueprint, Iterable[Blueprint], BlueprintGroup]): Blueprint object or (list, tuple) thereof.
            url_prefix (Optional[str]): Prefix for all URLs bound to the blueprint. Defaults to `None`.
            version (Optional[Union[int, float, str]]): Version prefix for URLs. Defaults to `None`.
            strict_slashes (Optional[bool]): Enforce the trailing slashes. Defaults to `None`.
            version_prefix (Optional[str]): Prefix for version. Defaults to `None`.
            name_prefix (Optional[str]): Prefix for the blueprint name. Defaults to `None`.

        Example:
            ```python
            app = Sanic("TestApp")
            bp = Blueprint('TestBP')

            @bp.route('/route')
            def handler(request):
                return text('Hello, Blueprint!')

            app.blueprint(bp, url_prefix='/blueprint')
            ```
        """  # noqa: E501
        options: dict[str, Any] = {}
        if url_prefix is not None:
            options["url_prefix"] = url_prefix
        if version is not None:
            options["version"] = version
        if strict_slashes is not None:
            options["strict_slashes"] = strict_slashes
        if version_prefix is not None:
            options["version_prefix"] = version_prefix
        if name_prefix is not None:
            options["name_prefix"] = name_prefix
        if isinstance(blueprint, (Iterable, BlueprintGroup)):
            for item in blueprint:
                params: dict[str, Any] = {**options}
                if isinstance(blueprint, BlueprintGroup):
                    merge_from = [
                        options.get("url_prefix", ""),
                        blueprint.url_prefix or "",
                    ]
                    if not isinstance(item, BlueprintGroup):
                        merge_from.append(item.url_prefix or "")
                    merged_prefix = "/".join(
                        str(u).strip("/") for u in merge_from if u
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
                    name_prefix = getattr(blueprint, "name_prefix", None)
                    if name_prefix and "name_prefix" not in params:
                        params["name_prefix"] = name_prefix
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

        This method constructs URLs for a given view name, taking into account
        various special keyword arguments that can be used to modify the resulting
        URL. It can handle internal routing as well as external URLs with different
        schemes.

        There are several special keyword arguments that can be used to modify
        the URL that is built. They each begin with an underscore. They are:

        - `_anchor`
        - `_external`
        - `_host`
        - `_server`
        - `_scheme`

        Args:
            view_name (str): String referencing the view name.
            _anchor (str): Adds an "#anchor" to the end.
            _scheme (str): Should be either "http" or "https", default is "http".
            _external (bool): Whether to return the path or a full URL with scheme and host.
            _host (str): Used when one or more hosts are defined for a route to tell Sanic which to use.
            _server (str): If not using "_host", this will be used for defining the hostname of the URL.
            **kwargs: Keys and values that are used to build request parameters and
                    query string arguments.

        Raises:
            URLBuildError: If there are issues with constructing the URL.

        Returns:
            str: The built URL.

        Examples:
            Building a URL for a specific view with parameters:
            ```python
            url_for('view_name', param1='value1', param2='value2')
            # /view-name?param1=value1&param2=value2
            ```

            Creating an external URL with a specific scheme and anchor:
            ```python
            url_for('view_name', _scheme='https', _external=True, _anchor='section1')
            # https://example.com/view-name#section1
            ```

            Creating a URL with a specific host:
            ```python
            url_for('view_name', _host='subdomain.example.com')
            # http://subdomain.example.com/view-name
        """  # noqa: E501
        # find the route by the supplied view name
        kw: dict[str, str] = {}
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
                # Replace http/https with ws/wss for WebSocket handlers
                if route.extra.websocket:
                    scheme = scheme.replace("http", "ws")

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
                    if param_info.cast is not str:
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
    ) -> None:  # no cov
        """A handler that catches specific exceptions and outputs a response.

        .. note::
            This method is typically used internally, and you should not need
            to call it directly.

        Args:
            request (Request): The current request object.
            exception (BaseException): The exception that was raised.
            run_middleware (bool): Whether to run middleware. Defaults
                to `True`.

        Raises:
            ServerError: response 500.
        """
        response = None
        if not getattr(exception, "__dispatched__", False):
            ...  # DO NOT REMOVE THIS LINE. IT IS NEEDED FOR TOUCHUP.
            await self.dispatch(
                "server.exception.report",
                context={"exception": exception},
            )
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
            try:
                middleware = (
                    request.route and request.route.extra.request_middleware
                ) or self.request_middleware
                response = await self._run_request_middleware(
                    request, middleware
                )
            except Exception as e:
                return await self.handle_exception(request, e, False)
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

    async def handle_request(self, request: Request) -> None:  # no cov
        """Handles a request by dispatching it to the appropriate handler.

        .. note::
            This method is typically used internally, and you should not need
            to call it directly.

        Args:
            request (Request): The current request object.

        Raises:
            ServerError: response 500.
        """
        __tracebackhide__ = True

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
                ResponseStream,
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
                        "'None' was returned while requesting a "
                        "handler from the router"
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

        except CancelledError:  # type: ignore
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

        await self.dispatch(
            "websocket.handler.before",
            inline=True,
            context={"request": request, "websocket": ws},
            fail_not_found=False,
        )
        # schedule the application handler
        # its future is kept in self.websocket_tasks in case it
        # needs to be cancelled due to the server being stopped
        fut = ensure_future(handler(request, ws, *args, **kwargs))
        self.websocket_tasks.add(fut)
        cancelled = False
        try:
            await fut
            await self.dispatch(
                "websocket.handler.after",
                inline=True,
                context={"request": request, "websocket": ws},
                reverse=True,
                fail_not_found=False,
            )
        except (CancelledError, ConnectionClosed):  # type: ignore
            cancelled = True
        except Exception as e:
            self.error_handler.log(request, e)
            await self.dispatch(
                "websocket.handler.exception",
                inline=True,
                context={"request": request, "websocket": ws, "exception": e},
                reverse=True,
                fail_not_found=False,
            )
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
    def test_client(self) -> SanicTestClient:  # type: ignore # noqa
        """A testing client that uses httpx and a live running server to reach into the application to execute handlers.

        This property is available if the `sanic-testing` package is installed.

        See [Test Clients](/en/plugins/sanic-testing/clients#wsgi-client-sanictestclient) for details.

        Returns:
            SanicTestClient: A testing client from the `sanic-testing` package.
        """  # noqa: E501
        if self._test_client:
            return self._test_client
        elif self._test_manager:
            return self._test_manager.test_client
        from sanic_testing.testing import SanicTestClient  # type: ignore

        self._test_client = SanicTestClient(self)
        return self._test_client

    @property
    def asgi_client(self) -> SanicASGITestClient:  # type: ignore # noqa
        """A testing client that uses ASGI to reach into the application to execute handlers.

        This property is available if the `sanic-testing` package is installed.

        See [Test Clients](/en/plugins/sanic-testing/clients#asgi-async-client-sanicasgitestclient) for details.

        Returns:
            SanicASGITestClient: A testing client from the `sanic-testing` package.
        """  # noqa: E501
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
        async def do(task):
            try:
                if callable(task):
                    try:
                        task = task(app)
                    except TypeError:
                        task = task()
                if isawaitable(task):
                    await task
            except CancelledError:
                error_logger.warning(
                    f"Task {task} was cancelled before it completed."
                )
                raise
            except Exception as e:
                await app.dispatch(
                    "server.exception.report",
                    context={"exception": e},
                )
                raise

        return do(task)

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
        tsk: Task = task
        if not isinstance(task, Future):
            prepped = cls._prep_task(task, app, loop)
            tsk = loop.create_task(prepped, name=name)

        if name and register:
            app._task_registry[name] = tsk

        return tsk

    @staticmethod
    async def dispatch_delayed_tasks(
        app: Sanic,
        loop: AbstractEventLoop,
    ) -> None:
        """Signal handler for dispatching delayed tasks.

        This is used to dispatch tasks that were added before the loop was
        started, and will be called after the loop has started. It is
        not typically used directly.

        Args:
            app (Sanic): The Sanic application instance.
            loop (AbstractEventLoop): The event loop in which the tasks are
                being run.

        Returns:
            None
        """
        for name in app._delayed_tasks:
            await app.dispatch(name, context={"app": app, "loop": loop})
        app._delayed_tasks.clear()

    @staticmethod
    async def run_delayed_task(
        app: Sanic,
        loop: AbstractEventLoop,
        task: Union[Future[Any], Task[Any], Awaitable[Any]],
    ) -> None:
        """Executes a delayed task within the context of a given app and loop.

        This method prepares a given task by invoking the app's private
        `_prep_task` method and then awaits the execution of the prepared task.

        Args:
            app (Any): The application instance on which the task will
                be executed.
            loop (AbstractEventLoop): The event loop where the task will
                be scheduled.
            task (Task[Any]): The task function that will be prepared
                and executed.

        Returns:
            None
        """
        prepped = app._prep_task(task, app, loop)
        await prepped

    def add_task(
        self,
        task: Union[Future[Any], Coroutine[Any, Any, Any], Awaitable[Any]],
        *,
        name: Optional[str] = None,
        register: bool = True,
    ) -> Optional[Task[Any]]:
        """Schedule a task to run later, after the loop has started.

        While this is somewhat similar to `asyncio.create_task`, it can be
        used before the loop has started (in which case it will run after the
        loop has started in the `before_server_start` listener).

        Naming tasks is a good practice as it allows you to cancel them later,
        and allows Sanic to manage them when the server is stopped, if needed.

        [See user guide re: background tasks](/en/guide/basics/tasks#background-tasks)

        Args:
            task (Union[Future[Any], Coroutine[Any, Any, Any], Awaitable[Any]]):
                The future, coroutine, or awaitable to schedule.
            name (Optional[str], optional): The name of the task, if needed for
                later reference. Defaults to `None`.
            register (bool, optional): Whether to register the task. Defaults
                to `True`.

        Returns:
            Optional[Task[Any]]: The task that was scheduled, if applicable.
        """  # noqa: E501
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

    @overload
    def get_task(
        self, name: str, *, raise_exception: Literal[True]
    ) -> Task: ...

    @overload
    def get_task(
        self, name: str, *, raise_exception: Literal[False]
    ) -> Optional[Task]: ...

    @overload
    def get_task(
        self, name: str, *, raise_exception: bool
    ) -> Optional[Task]: ...

    def get_task(
        self, name: str, *, raise_exception: bool = True
    ) -> Optional[Task]:
        """Get a named task.

        This method is used to get a task by its name. Optionally, you can
        control whether an exception should be raised if the task is not found.

        Args:
            name (str): The name of the task to be retrieved.
            raise_exception (bool): If `True`, an exception will be raised if
                the task is not found. Defaults to `True`.

        Returns:
            Optional[Task]: The task, if found.
        """
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
        """Cancel a named task.

        This method is used to cancel a task by its name. Optionally, you can
        provide a message that describes why the task was canceled, and control
        whether an exception should be raised if the task is not found.

        Args:
            name (str): The name of the task to be canceled.
            msg (Optional[str]): Optional message describing why the task was canceled. Defaults to None.
            raise_exception (bool): If True, an exception will be raised if the task is not found. Defaults to True.

        Example:
            ```python
            async def my_task():
                try:
                    await asyncio.sleep(10)
                except asyncio.CancelledError as e:
                    current_task = asyncio.current_task()
                    print(f"Task {current_task.get_name()} was cancelled. {e}")
                    # Task sleepy_task was cancelled. No more sleeping!


            @app.before_server_start
            async def before_start(app):
                app.add_task(my_task, name="sleepy_task")
                await asyncio.sleep(1)
                await app.cancel_task("sleepy_task", msg="No more sleeping!")
            ```
        """  # noqa: E501
        task = self.get_task(name, raise_exception=raise_exception)
        if task and not task.cancelled():
            args: tuple[str, ...] = ()
            if msg:
                args = (msg,)
            task.cancel(*args)
            try:
                await task
            except CancelledError:
                ...

    def purge_tasks(self) -> None:
        """Purges completed and cancelled tasks from the task registry.

        This method iterates through the task registry, identifying any tasks
        that are either done or cancelled, and then removes those tasks,
        leaving only the pending tasks in the registry.
        """
        for key, task in self._task_registry.items():
            if task is None:
                continue
            if task.done() or task.cancelled():
                self._task_registry[key] = None

        self._task_registry = {
            k: v for k, v in self._task_registry.items() if v is not None
        }

    def shutdown_tasks(
        self, timeout: Optional[float] = None, increment: float = 0.1
    ) -> None:
        """Cancel all tasks except the server task.

        This method is used to cancel all tasks except the server task. It
        iterates through the task registry, cancelling all tasks except the
        server task, and then waits for the tasks to complete. Optionally, you
        can provide a timeout and an increment to control how long the method
        will wait for the tasks to complete.

        Args:
            timeout (Optional[float]): The amount of time to wait for the tasks
                to complete. Defaults to `None`.
            increment (float): The amount of time to wait between checks for
                whether the tasks have completed. Defaults to `0.1`.
        """
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
    def tasks(self) -> Iterable[Task[Any]]:
        """The tasks that are currently registered with the application.

        Returns:
            Iterable[Task[Any]]: The tasks that are currently registered with
                the application.
        """
        return (
            task
            for task in iter(self._task_registry.values())
            if task is not None
        )

    # -------------------------------------------------------------------- #
    # ASGI
    # -------------------------------------------------------------------- #

    async def __call__(self, scope, receive, send):
        """
        To be ASGI compliant, our instance must be a callable that accepts
        three arguments: scope, receive, send. See the ASGI reference for more
        details: https://asgi.readthedocs.io/en/latest
        """
        if scope["type"] == "lifespan":
            setup_logging(self.state.is_debug, self.config.NO_COLOR)
            self.asgi = True
            self.motd("")
            self._asgi_lifespan = Lifespan(self, scope, receive, send)
            await self._asgi_lifespan()
        else:
            self._asgi_app = await ASGIApp.create(self, scope, receive, send)
            await self._asgi_app()

    _asgi_single_callable = True  # We conform to ASGI 3.0 single-callable

    # -------------------------------------------------------------------- #
    # Configuration
    # -------------------------------------------------------------------- #

    def update_config(self, config: Union[bytes, str, dict, Any]) -> None:
        """Update the application configuration.

        This method is used to update the application configuration. It can
        accept a configuration object, a dictionary, or a path to a file that
        contains a configuration object or dictionary.

        See [Configuration](/en/guide/deployment/configuration) for details.

        Args:
            config (Union[bytes, str, dict, Any]): The configuration object,
                dictionary, or path to a configuration file.
        """

        self.config.update_config(config)

    @property
    def asgi(self) -> bool:
        """Whether the app is running in ASGI mode."""
        return self.state.asgi

    @asgi.setter
    def asgi(self, value: bool):
        self.state.asgi = value

    @property
    def debug(self) -> bool:
        """Whether the app is running in debug mode."""
        return self.state.is_debug

    @property
    def auto_reload(self) -> bool:
        """Whether the app is running in auto-reload mode."""
        return self.config.AUTO_RELOAD

    @auto_reload.setter
    def auto_reload(self, value: bool):
        self.config.AUTO_RELOAD = value
        self.state.auto_reload = value

    @property
    def state(self) -> ApplicationState:  # type: ignore
        """The application state.

        Returns:
            ApplicationState: The current state of the application.
        """
        return self._state

    @property
    def reload_dirs(self) -> set[Path]:
        """The directories that are monitored for auto-reload.

        Returns:
            Set[str]: The set of directories that are monitored for
                auto-reload.
        """
        return self.state.reload_dirs

    # -------------------------------------------------------------------- #
    # Sanic Extensions
    # -------------------------------------------------------------------- #

    @property
    def ext(self) -> Extend:
        """Convenience property for accessing Sanic Extensions.

        This property is available if the `sanic-ext` package is installed.

        See [Sanic Extensions](/en/plugins/sanic-ext/getting-started)
            for details.

        Returns:
            Extend: The Sanic Extensions instance.

        Examples:
            A typical use case might be for registering a dependency injection.
            ```python
            app.ext.dependency(SomeObject())
            ```
        """
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
        extensions: Optional[list[type[Extension]]] = None,
        built_in_extensions: bool = True,
        config: Optional[Union[Config, dict[str, Any]]] = None,
        **kwargs,
    ) -> Extend:
        """Extend Sanic with additional functionality using Sanic Extensions.

        This method enables you to add one or more Sanic Extensions to the
        current Sanic instance. It allows for more control over the Extend
        object, such as enabling or disabling built-in extensions or providing
        custom configuration.

        See [Sanic Extensions](/en/plugins/sanic-ext/getting-started)
            for details.

        Args:
            extensions (Optional[List[Type[Extension]]], optional): A list of
                extensions to add. Defaults to `None`, meaning only built-in
                extensions are added.
            built_in_extensions (bool, optional): Whether to enable built-in
                extensions. Defaults to `True`.
            config (Optional[Union[Config, Dict[str, Any]]], optional):
                Optional custom configuration for the extensions. Defaults
                to `None`.
            **kwargs: Additional keyword arguments that might be needed by
                specific extensions.

        Returns:
            Extend: The Sanic Extensions instance.

        Raises:
            RuntimeError: If an attempt is made to extend Sanic after Sanic
                Extensions has already been set up.

        Examples:
            A typical use case might be to add a custom extension along with
                built-in ones.
            ```python
            app.extend(
                extensions=[MyCustomExtension],
                built_in_extensions=True
            )
            ```
        """
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
    def register_app(cls, app: Sanic) -> None:
        """Register a Sanic instance with the class registry.

        This method adds a Sanic application instance to the class registry,
        which is used for tracking all instances of the application. It is
        usually used internally, but can be used to register an application
        that may have otherwise been created outside of the class registry.

        Args:
            app (Sanic): The Sanic instance to be registered.

        Raises:
            SanicException: If the app is not an instance of Sanic or if the
                name of the app is already in use (unless in test mode).

        Examples:
            ```python
            Sanic.register_app(my_app)
            ```
        """
        if not isinstance(app, cls):
            raise SanicException("Registered app must be an instance of Sanic")

        name = app.name
        if name in cls._app_registry and not cls.test_mode:
            raise SanicException(f'Sanic app name "{name}" already in use.')

        cls._app_registry[name] = app

    @classmethod
    def unregister_app(cls, app: Sanic) -> None:
        """Unregister a Sanic instance from the class registry.

        This method removes a previously registered Sanic application instance
        from the class registry. This can be useful for cleanup purposes,
        especially in testing or when an app instance is no longer needed. But,
        it is typically used internally and should not be needed in most cases.

        Args:
            app (Sanic): The Sanic instance to be unregistered.

        Raises:
            SanicException: If the app is not an instance of Sanic.

        Examples:
            ```python
            Sanic.unregister_app(my_app)
            ```
        """
        if not isinstance(app, cls):
            raise SanicException("Registered app must be an instance of Sanic")

        name = app.name
        if name in cls._app_registry:
            del cls._app_registry[name]

    @classmethod
    def get_app(
        cls, name: Optional[str] = None, *, force_create: bool = False
    ) -> Sanic:
        """Retrieve an instantiated Sanic instance by name.

        This method is best used when needing to get access to an already
        defined application instance in another part of an app.

        .. warning::
            Be careful when using this method in the global scope as it is
            possible that the import path running will cause it to error if
            the imported global scope runs before the application instance
            is created.

            It is typically best used in a function or method that is called
            after the application instance has been created.

            ```python
            def setup_routes():
                app = Sanic.get_app()
                app.add_route(handler_1, '/route1')
                app.add_route(handler_2, '/route2')
            ```

        Args:
            name (Optional[str], optional): Name of the application instance
                to retrieve. When not specified, it will return the only
                application instance if there is only one. If not specified
                and there are multiple application instances, it will raise
                an exception. Defaults to `None`.
            force_create (bool, optional): If `True` and the named app does
                not exist, a new instance will be created. Defaults to `False`.

        Returns:
            Sanic: The requested Sanic app instance.

        Raises:
            SanicException: If there are multiple or no Sanic apps found, or
                if the specified name is not found.


        Example:
            ```python
            app1 = Sanic("app1")
            app2 = Sanic.get_app("app1")  # app2 is the same instance as app1
            ```
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

    @contextmanager
    def amend(self) -> Iterator[None]:
        """Context manager to allow changes to the app after it has started.

        Typically, once an application has started and is running, you cannot
        make certain changes, like adding routes, middleware, or signals. This
        context manager allows you to make those changes, and then finalizes
        the app again when the context manager exits.

        Yields:
            None

        Example:
            ```python
            with app.amend():
                app.add_route(handler, '/new_route')
            ```
        """
        if not self.state.is_started:
            yield
        else:
            do_router = self.router.finalized
            do_signal_router = self.signal_router.finalized
            if do_router:
                self.router.reset()
            if do_signal_router:
                self.signal_router.reset()
            yield
            if do_signal_router:
                self.signalize(cast(bool, self.config.TOUCHUP))
            if do_router:
                self.finalize()

    def finalize(self) -> None:
        """Finalize the routing configuration for the Sanic application.

        This method completes the routing setup by calling the router's
        finalize method, and it also finalizes any middleware that has been
        added to the application. If the application is not in test mode,
        any finalization errors will be raised.

        Finalization consists of identifying defined routes and optimizing
        Sanic's performance to meet the application's specific needs. If
        you are manually adding routes, after Sanic has started, you will
        typically want to use the  `amend` context manager rather than
        calling this method directly.

        .. note::
            This method is usually called internally during the server setup
            process and does not typically need to be invoked manually.

        Raises:
            FinalizationError: If there is an error during the finalization
                process, and the application is not in test mode.

        Example:
            ```python
            app.finalize()
            ```
        """
        try:
            self.router.finalize()
        except FinalizationError as e:
            if not Sanic.test_mode:
                raise e
        self.finalize_middleware()

    def signalize(self, allow_fail_builtin: bool = True) -> None:
        """Finalize the signal handling configuration for the Sanic application.

        This method completes the signal handling setup by calling the signal
        router's finalize method. If the application is not in test mode,
        any finalization errors will be raised.

        Finalization consists of identifying defined signaliz and optimizing
        Sanic's performance to meet the application's specific needs. If
        you are manually adding signals, after Sanic has started, you will
        typically want to use the  `amend` context manager rather than
        calling this method directly.

        .. note::
            This method is usually called internally during the server setup
            process and does not typically need to be invoked manually.

        Args:
            allow_fail_builtin (bool, optional): If set to `True`, will allow
                built-in signals to fail during the finalization process.
                Defaults to `True`.

        Raises:
            FinalizationError: If there is an error during the signal
                finalization process, and the application is not in test mode.

        Example:
            ```python
            app.signalize(allow_fail_builtin=False)
            ```
        """  # noqa: E501
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

        route_names = [route.extra.ident for route in self.router.routes]
        duplicates = {
            name for name in route_names if route_names.count(name) > 1
        }
        if duplicates:
            names = ", ".join(duplicates)
            message = (
                f"Duplicate route names detected: {names}. You should rename "
                "one or more of them explicitly by using the `name` param, "
                "or changing the implicit name derived from the class and "
                "function name. For more details, please see "
                "https://sanic.dev/en/guide/release-notes/v23.3.html#duplicated-route-names-are-no-longer-allowed"  # noqa
            )
            raise ServerError(message)

        Sanic._check_uvloop_conflict()

        # Startup time optimizations
        if self.state.primary:
            # TODO:
            # - Raise warning if secondary apps have error handler config
            if self.config.TOUCHUP:
                TouchUp.run(self)

        self.state.is_started = True

    def ack(self) -> None:
        """Shorthand to send an ack message to the Server Manager.

        In general, this should usually not need to be called manually.
        It is used to tell the Manager that a process is operational and
        ready to begin operation.
        """
        if hasattr(self, "multiplexer"):
            self.multiplexer.ack()

    def set_serving(self, serving: bool) -> None:
        """Set the serving state of the application.

        This method is used to set the serving state of the application.
        It is used internally by Sanic and should not typically be called
        manually.

        Args:
            serving (bool): Whether the application is serving.
        """
        self.state.is_running = serving
        if hasattr(self, "multiplexer"):
            self.multiplexer.set_serving(serving)

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
        passthru: Optional[dict[str, Any]] = None,
    ) -> Sanic:
        """Refresh the application instance. **This is used internally by Sanic**.

        .. warning::
            This method is intended for internal use only and should not be
            called directly.

        Args:
            passthru (Optional[Dict[str, Any]], optional): Optional dictionary
                of attributes to pass through to the new instance. Defaults to
                `None`.

        Returns:
            Sanic: The refreshed application instance.
        """  # noqa: E501
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
    def inspector(self) -> Inspector:
        """An instance of Inspector for accessing the application's state.

        This can only be accessed from a worker process, and only if the
        inspector has been enabled.

        See [Inspector](/en/guide/deployment/inspector) for details.

        Returns:
            Inspector: An instance of Inspector.
        """
        if environ.get("SANIC_WORKER_PROCESS") or not self._inspector:
            raise SanicException(
                "Can only access the inspector from the main process "
                "after main_process_start has run. For example, you most "
                "likely want to use it inside the @app.main_process_ready "
                "event listener."
            )
        return self._inspector

    @property
    def manager(self) -> WorkerManager:
        """
        Property to access the WorkerManager instance.

        This property provides access to the WorkerManager object controlling
        the worker processes. It can only be accessed from the main process.

        .. note::
            Make sure to only access this property from the main process,
            as attempting to do so from a worker process will result
            in an exception.

        See [WorkerManager](/en/guide/deployment/manager) for details.

        Returns:
            WorkerManager: The manager responsible for managing
                worker processes.

        Raises:
            SanicException: If an attempt is made to access the manager
                from a worker process or if the manager is not initialized.

        Example:
            ```python
            app.manager.manage(...)
            ```
        """

        if environ.get("SANIC_WORKER_PROCESS") or not self._manager:
            raise SanicException(
                "Can only access the manager from the main process "
                "after main_process_start has run. For example, you most "
                "likely want to use it inside the @app.main_process_ready "
                "event listener."
            )
        return self._manager
