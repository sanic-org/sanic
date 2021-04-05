from __future__ import annotations

import asyncio

from collections import defaultdict
from types import SimpleNamespace
from typing import TYPE_CHECKING, Dict, Iterable, List, Optional, Set, Union

from sanic_routing.exceptions import NotFound  # type: ignore
from sanic_routing.route import Route  # type: ignore

from sanic.base import BaseSanic
from sanic.blueprint_group import BlueprintGroup
from sanic.exceptions import SanicException
from sanic.models.futures import FutureRoute, FutureStatic
from sanic.models.handler_types import (
    ListenerType,
    MiddlewareType,
    RouteHandler,
)


if TYPE_CHECKING:
    from sanic import Sanic  # noqa


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
    :param host: IP Address of FQDN for the sanic server to use.
    :param version: Blueprint Version
    :param strict_slashes: Enforce the API urls are requested with a
        training */*
    """

    __fake_slots__ = (
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
        "name",
        "routes",
        "statics",
        "strict_slashes",
        "url_prefix",
        "version",
        "websocket_routes",
    )

    def __init__(
        self,
        name: str,
        url_prefix: Optional[str] = None,
        host: Optional[str] = None,
        version: Optional[int] = None,
        strict_slashes: Optional[bool] = None,
    ):
        super().__init__()

        self._apps: Set[Sanic] = set()
        self.ctx = SimpleNamespace()
        self.exceptions: List[RouteHandler] = []
        self.host = host
        self.listeners: Dict[str, List[ListenerType]] = {}
        self.middlewares: List[MiddlewareType] = []
        self.name = name
        self.routes: List[Route] = []
        self.statics: List[RouteHandler] = []
        self.strict_slashes = strict_slashes
        self.url_prefix = (
            url_prefix[:-1]
            if url_prefix and url_prefix.endswith("/")
            else url_prefix
        )
        self.version = version
        self.websocket_routes: List[Route] = []

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

    def route(self, *args, **kwargs):
        kwargs["apply"] = False
        return super().route(*args, **kwargs)

    def static(self, *args, **kwargs):
        kwargs["apply"] = False
        return super().static(*args, **kwargs)

    def middleware(self, *args, **kwargs):
        kwargs["apply"] = False
        return super().middleware(*args, **kwargs)

    def listener(self, *args, **kwargs):
        kwargs["apply"] = False
        return super().listener(*args, **kwargs)

    def exception(self, *args, **kwargs):
        kwargs["apply"] = False
        return super().exception(*args, **kwargs)

    def signal(self, event: str, *args, **kwargs):
        kwargs["apply"] = False
        return super().signal(event, *args, **kwargs)

    @staticmethod
    def group(*blueprints, url_prefix="", version=None, strict_slashes=None):
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
                elif isinstance(i, BlueprintGroup):
                    yield from i.blueprints
                else:
                    yield i

        bps = BlueprintGroup(
            url_prefix=url_prefix,
            version=version,
            strict_slashes=strict_slashes,
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

        routes = []
        middleware = []
        exception_handlers = []
        listeners = defaultdict(list)

        # Routes
        for future in self._future_routes:
            # attach the blueprint name to the handler so that it can be
            # prefixed properly in the router
            future.handler.__blueprintname__ = self.name
            # Prepend the blueprint URI prefix if available
            uri = url_prefix + future.uri if url_prefix else future.uri

            strict_slashes = (
                self.strict_slashes
                if future.strict_slashes is None
                and self.strict_slashes is not None
                else future.strict_slashes
            )
            name = app._generate_name(future.name)

            apply_route = FutureRoute(
                future.handler,
                uri[1:] if uri.startswith("//") else uri,
                future.methods,
                future.host or self.host,
                strict_slashes,
                future.stream,
                future.version or self.version,
                name,
                future.ignore_body,
                future.websocket,
                future.subprotocols,
                future.unquote,
                future.static,
            )

            route = app._apply_route(apply_route)
            operation = (
                routes.extend if isinstance(route, list) else routes.append
            )
            operation(route)

        # Static Files
        for future in self._future_statics:
            # Prepend the blueprint URI prefix if available
            uri = url_prefix + future.uri if url_prefix else future.uri
            apply_route = FutureStatic(uri, *future[1:])
            route = app._apply_static(apply_route)
            routes.append(route)

        route_names = [route.name for route in routes if route]

        # Middleware
        if route_names:
            for future in self._future_middleware:
                middleware.append(app._apply_middleware(future, route_names))

        # Exceptions
        for future in self._future_exceptions:
            exception_handlers.append(app._apply_exception_handler(future))

        # Event listeners
        for listener in self._future_listeners:
            listeners[listener.event].append(app._apply_listener(listener))

        for signal in self._future_signals:
            signal.condition.update({"blueprint": self.name})
            app._apply_signal(signal)

        self.routes = [route for route in routes if isinstance(route, Route)]

        # Deprecate these in 21.6
        self.websocket_routes = [
            route for route in self.routes if route.ctx.websocket
        ]
        self.middlewares = middleware
        self.exceptions = exception_handlers
        self.listeners = dict(listeners)

    async def dispatch(self, *args, **kwargs):
        condition = kwargs.pop("condition", {})
        condition.update({"blueprint": self.name})
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
            [event.wait() for event in events],
            return_when=asyncio.FIRST_COMPLETED,
            timeout=timeout,
        )
