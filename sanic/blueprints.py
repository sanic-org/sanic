from __future__ import annotations

import asyncio

from collections import defaultdict
from copy import deepcopy
from functools import wraps
from inspect import isfunction
from itertools import chain
from types import SimpleNamespace
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

from sanic_routing.exceptions import NotFound
from sanic_routing.route import Route

from sanic.base.root import BaseSanic
from sanic.blueprint_group import BlueprintGroup
from sanic.exceptions import SanicException
from sanic.helpers import Default, _default
from sanic.models.futures import FutureRoute, FutureStatic
from sanic.models.handler_types import (
    ListenerType,
    MiddlewareType,
    RouteHandler,
)


if TYPE_CHECKING:
    from sanic import Sanic


def lazy(func, as_decorator=True):
    @wraps(func)
    def decorator(bp, *args, **kwargs):
        nonlocal as_decorator
        kwargs["apply"] = False
        pass_handler = None

        if args and isfunction(args[0]):
            as_decorator = False

        def wrapper(handler):
            future = func(bp, *args, **kwargs)
            if as_decorator:
                future = future(handler)

            if bp.registered:
                for app in bp.apps:
                    bp.register(app, {})

            return future

        return wrapper if as_decorator else wrapper(pass_handler)

    return decorator


class Blueprint(BaseSanic):
    """
    In *Sanic* terminology, a **Blueprint** is a logical collection of
    URLs that perform a specific set of tasks which can be identified by
    a unique name.

    It is the main tool for grouping functionality and similar endpoints.

    `See user guide re: blueprints
    <https://sanicframework.org/guide/best-practices/blueprints.html>`__

    :param name: unique name of the blueprint
    :param url_prefix: URL to be prefixed before all route URLs
    :param host: IP Address or FQDN for the sanic server to use.
    :param version: Blueprint Version
    :param strict_slashes: Enforce the API urls are requested with a
        trailing */*
    """

    __slots__ = (
        "_apps",
        "_future_routes",
        "_future_statics",
        "_future_middleware",
        "_future_listeners",
        "_future_exceptions",
        "_future_signals",
        "ctx",
        "exceptions",
        "host",
        "listeners",
        "middlewares",
        "routes",
        "statics",
        "strict_slashes",
        "url_prefix",
        "version",
        "version_prefix",
        "websocket_routes",
    )

    def __init__(
        self,
        name: str = None,
        url_prefix: Optional[str] = None,
        host: Optional[Union[List[str], str]] = None,
        version: Optional[Union[int, str, float]] = None,
        strict_slashes: Optional[bool] = None,
        version_prefix: str = "/v",
    ):
        super().__init__(name=name)
        self.reset()
        self.ctx = SimpleNamespace()
        self.host = host
        self.strict_slashes = strict_slashes
        self.url_prefix = (
            url_prefix[:-1]
            if url_prefix and url_prefix.endswith("/")
            else url_prefix
        )
        self.version = version
        self.version_prefix = version_prefix

    def __repr__(self) -> str:
        args = ", ".join(
            [
                f'{attr}="{getattr(self, attr)}"'
                if isinstance(getattr(self, attr), str)
                else f"{attr}={getattr(self, attr)}"
                for attr in (
                    "name",
                    "url_prefix",
                    "host",
                    "version",
                    "strict_slashes",
                )
            ]
        )
        return f"Blueprint({args})"

    @property
    def apps(self):
        if not self._apps:
            raise SanicException(
                f"{self} has not yet been registered to an app"
            )
        return self._apps

    @property
    def registered(self) -> bool:
        return bool(self._apps)

    exception = lazy(BaseSanic.exception)
    listener = lazy(BaseSanic.listener)
    middleware = lazy(BaseSanic.middleware)
    route = lazy(BaseSanic.route)
    signal = lazy(BaseSanic.signal)
    static = lazy(BaseSanic.static, as_decorator=False)

    def reset(self):
        self._apps: Set[Sanic] = set()
        self.exceptions: List[RouteHandler] = []
        self.listeners: Dict[str, List[ListenerType[Any]]] = {}
        self.middlewares: List[MiddlewareType] = []
        self.routes: List[Route] = []
        self.statics: List[RouteHandler] = []
        self.websocket_routes: List[Route] = []

    def copy(
        self,
        name: str,
        url_prefix: Optional[Union[str, Default]] = _default,
        version: Optional[Union[int, str, float, Default]] = _default,
        version_prefix: Union[str, Default] = _default,
        strict_slashes: Optional[Union[bool, Default]] = _default,
        with_registration: bool = True,
        with_ctx: bool = False,
    ):
        """
        Copy a blueprint instance with some optional parameters to
        override the values of attributes in the old instance.

        :param name: unique name of the blueprint
        :param url_prefix: URL to be prefixed before all route URLs
        :param version: Blueprint Version
        :param version_prefix: the prefix of the version number shown in the
            URL.
        :param strict_slashes: Enforce the API urls are requested with a
            trailing */*
        :param with_registration: whether register new blueprint instance with
            sanic apps that were registered with the old instance or not.
        :param with_ctx: whether ``ctx`` will be copied or not.
        """

        attrs_backup = {
            "_apps": self._apps,
            "routes": self.routes,
            "websocket_routes": self.websocket_routes,
            "middlewares": self.middlewares,
            "exceptions": self.exceptions,
            "listeners": self.listeners,
            "statics": self.statics,
        }

        self.reset()
        new_bp = deepcopy(self)
        new_bp.name = name

        if not isinstance(url_prefix, Default):
            new_bp.url_prefix = url_prefix
        if not isinstance(version, Default):
            new_bp.version = version
        if not isinstance(strict_slashes, Default):
            new_bp.strict_slashes = strict_slashes
        if not isinstance(version_prefix, Default):
            new_bp.version_prefix = version_prefix

        for key, value in attrs_backup.items():
            setattr(self, key, value)

        if with_registration and self._apps:
            if new_bp._future_statics:
                raise SanicException(
                    "Static routes registered with the old blueprint instance,"
                    " cannot be registered again."
                )
            for app in self._apps:
                app.blueprint(new_bp)

        if not with_ctx:
            new_bp.ctx = SimpleNamespace()

        return new_bp

    @staticmethod
    def group(
        *blueprints: Union[Blueprint, BlueprintGroup],
        url_prefix: Optional[str] = None,
        version: Optional[Union[int, str, float]] = None,
        strict_slashes: Optional[bool] = None,
        version_prefix: str = "/v",
    ) -> BlueprintGroup:
        """
        Create a list of blueprints, optionally grouping them under a
        general URL prefix.

        :param blueprints: blueprints to be registered as a group
        :param url_prefix: URL route to be prepended to all sub-prefixes
        :param version: API Version to be used for Blueprint group
        :param strict_slashes: Indicate strict slash termination behavior
            for URL
        """

        def chain(nested) -> Iterable[Blueprint]:
            """itertools.chain() but leaves strings untouched"""
            for i in nested:
                if isinstance(i, (list, tuple)):
                    yield from chain(i)
                else:
                    yield i

        bps = BlueprintGroup(
            url_prefix=url_prefix,
            version=version,
            strict_slashes=strict_slashes,
            version_prefix=version_prefix,
        )
        for bp in chain(blueprints):
            bps.append(bp)
        return bps

    def register(self, app, options):
        """
        Register the blueprint to the sanic app.

        :param app: Instance of :class:`sanic.app.Sanic` class
        :param options: Options to be used while registering the
            blueprint into the app.
            *url_prefix* - URL Prefix to override the blueprint prefix
        """

        self._apps.add(app)
        url_prefix = options.get("url_prefix", self.url_prefix)
        opt_version = options.get("version", None)
        opt_strict_slashes = options.get("strict_slashes", None)
        opt_version_prefix = options.get("version_prefix", self.version_prefix)
        error_format = options.get(
            "error_format", app.config.FALLBACK_ERROR_FORMAT
        )

        routes = []
        middleware = []
        exception_handlers = []
        listeners = defaultdict(list)
        registered = set()

        # Routes
        for future in self._future_routes:
            # attach the blueprint name to the handler so that it can be
            # prefixed properly in the router
            future.handler.__blueprintname__ = self.name
            # Prepend the blueprint URI prefix if available
            uri = self._setup_uri(future.uri, url_prefix)

            version_prefix = self.version_prefix
            for prefix in (
                future.version_prefix,
                opt_version_prefix,
            ):
                if prefix and prefix != "/v":
                    version_prefix = prefix
                    break

            version = self._extract_value(
                future.version, opt_version, self.version
            )
            strict_slashes = self._extract_value(
                future.strict_slashes, opt_strict_slashes, self.strict_slashes
            )

            name = app._generate_name(future.name)
            host = future.host or self.host
            if isinstance(host, list):
                host = tuple(host)

            apply_route = FutureRoute(
                future.handler,
                uri,
                future.methods,
                host,
                strict_slashes,
                future.stream,
                version,
                name,
                future.ignore_body,
                future.websocket,
                future.subprotocols,
                future.unquote,
                future.static,
                version_prefix,
                error_format,
                future.route_context,
            )

            if (self, apply_route) in app._future_registry:
                continue

            registered.add(apply_route)
            route = app._apply_route(apply_route)
            operation = (
                routes.extend if isinstance(route, list) else routes.append
            )
            operation(route)

        # Static Files
        for future in self._future_statics:
            # Prepend the blueprint URI prefix if available
            uri = self._setup_uri(future.uri, url_prefix)
            apply_route = FutureStatic(uri, *future[1:])

            if (self, apply_route) in app._future_registry:
                continue

            registered.add(apply_route)
            route = app._apply_static(apply_route)
            routes.append(route)

        route_names = [route.name for route in routes if route]

        if route_names:
            # Middleware
            for future in self._future_middleware:
                if (self, future) in app._future_registry:
                    continue
                middleware.append(app._apply_middleware(future, route_names))

            # Exceptions
            for future in self._future_exceptions:
                if (self, future) in app._future_registry:
                    continue
                exception_handlers.append(
                    app._apply_exception_handler(future, route_names)
                )

        # Event listeners
        for future in self._future_listeners:
            if (self, future) in app._future_registry:
                continue
            listeners[future.event].append(app._apply_listener(future))

        # Signals
        for future in self._future_signals:
            if (self, future) in app._future_registry:
                continue
            future.condition.update({"__blueprint__": self.name})
            # Force exclusive to be False
            app._apply_signal(tuple((*future[:-1], False)))

        self.routes += [route for route in routes if isinstance(route, Route)]
        self.websocket_routes += [
            route for route in self.routes if route.extra.websocket
        ]
        self.middlewares += middleware
        self.exceptions += exception_handlers
        self.listeners.update(dict(listeners))

        if self.registered:
            self.register_futures(
                self.apps,
                self,
                chain(
                    registered,
                    self._future_middleware,
                    self._future_exceptions,
                    self._future_listeners,
                    self._future_signals,
                ),
            )

    async def dispatch(self, *args, **kwargs):
        condition = kwargs.pop("condition", {})
        condition.update({"__blueprint__": self.name})
        kwargs["condition"] = condition
        await asyncio.gather(
            *[app.dispatch(*args, **kwargs) for app in self.apps]
        )

    def event(self, event: str, timeout: Optional[Union[int, float]] = None):
        events = set()
        for app in self.apps:
            signal = app.signal_router.name_index.get(event)
            if not signal:
                raise NotFound("Could not find signal %s" % event)
            events.add(signal.ctx.event)

        return asyncio.wait(
            [asyncio.create_task(event.wait()) for event in events],
            return_when=asyncio.FIRST_COMPLETED,
            timeout=timeout,
        )

    @staticmethod
    def _extract_value(*values):
        value = values[-1]
        for v in values:
            if v is not None:
                value = v
                break
        return value

    @staticmethod
    def _setup_uri(base: str, prefix: Optional[str]):
        uri = base
        if prefix:
            uri = prefix
            if base.startswith("/") and prefix.endswith("/"):
                uri += base[1:]
            else:
                uri += base

        return uri[1:] if uri.startswith("//") else uri

    @staticmethod
    def register_futures(
        apps: Set[Sanic], bp: Blueprint, futures: Sequence[Tuple[Any, ...]]
    ):
        for app in apps:
            app._future_registry.update(set((bp, item) for item in futures))
