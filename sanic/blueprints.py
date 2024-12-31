from __future__ import annotations

import asyncio

from collections import defaultdict
from collections.abc import Iterable, Iterator, MutableSequence, Sequence
from copy import deepcopy
from functools import partial, wraps
from inspect import isfunction
from itertools import chain
from types import SimpleNamespace
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Optional,
    Union,
    overload,
)

from sanic_routing.exceptions import NotFound
from sanic_routing.route import Route

from sanic.base.root import BaseSanic
from sanic.exceptions import SanicException
from sanic.helpers import Default, _default
from sanic.models.futures import FutureRoute, FutureSignal, FutureStatic
from sanic.models.handler_types import (
    ListenerType,
    MiddlewareType,
    RouteHandler,
)


if TYPE_CHECKING:
    from sanic import Sanic


def lazy(func, as_decorator=True):
    """Decorator to register a function to be called later.

    Args:
        func (Callable): Function to be called later.
        as_decorator (bool): Whether the function should be called
            immediately or not.
    """

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
    """A logical collection of URLs that consist of a similar logical domain.

    A Blueprint object is the main tool for grouping functionality and similar endpoints. It allows the developer to
    organize routes, exception handlers, middleware, and other web functionalities into separate, modular groups.

    See [Blueprints](/en/guide/best-practices/blueprints) for more information.

    Args:
        name (str): The name of the blueprint.
        url_prefix (Optional[str]): The URL prefix for all routes defined on this blueprint.
        host (Optional[Union[List[str], str]]): Host or list of hosts that this blueprint should respond to.
        version (Optional[Union[int, str, float]]): Version number of the API implemented by this blueprint.
        strict_slashes (Optional[bool]): Whether or not the URL should end with a slash.
        version_prefix (str): Prefix for the version. Default is "/v".
    """  # noqa: E501

    __slots__ = (
        "_apps",
        "_future_commands",
        "_future_routes",
        "_future_statics",
        "_future_middleware",
        "_future_listeners",
        "_future_exceptions",
        "_future_signals",
        "_allow_route_overwrite",
        "copied_from",
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
        name: str,
        url_prefix: Optional[str] = None,
        host: Optional[Union[list[str], str]] = None,
        version: Optional[Union[int, str, float]] = None,
        strict_slashes: Optional[bool] = None,
        version_prefix: str = "/v",
    ):
        super().__init__(name=name)
        self.reset()
        self._allow_route_overwrite = False
        self.copied_from = ""
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
    def apps(self) -> set[Sanic]:
        """Get the set of apps that this blueprint is registered to.

        Returns:
            Set[Sanic]: Set of apps that this blueprint is registered to.

        Raises:
            SanicException: If the blueprint has not yet been registered to
                an app.
        """
        if not self._apps:
            raise SanicException(
                f"{self} has not yet been registered to an app"
            )
        return self._apps

    @property
    def registered(self) -> bool:
        """Check if the blueprint has been registered to an app.

        Returns:
            bool: `True` if the blueprint has been registered to an app,
                `False` otherwise.
        """
        return bool(self._apps)

    exception = lazy(BaseSanic.exception)
    listener = lazy(BaseSanic.listener)
    middleware = lazy(BaseSanic.middleware)
    route = lazy(BaseSanic.route)
    signal = lazy(BaseSanic.signal)
    static = lazy(BaseSanic.static, as_decorator=False)

    def reset(self) -> None:
        """Reset the blueprint to its initial state."""
        self._apps: set[Sanic] = set()
        self._allow_route_overwrite = False
        self.exceptions: list[RouteHandler] = []
        self.listeners: dict[str, list[ListenerType[Any]]] = {}
        self.middlewares: list[MiddlewareType] = []
        self.routes: list[Route] = []
        self.statics: list[RouteHandler] = []
        self.websocket_routes: list[Route] = []

    def copy(
        self,
        name: str,
        url_prefix: Optional[Union[str, Default]] = _default,
        version: Optional[Union[int, str, float, Default]] = _default,
        version_prefix: Union[str, Default] = _default,
        allow_route_overwrite: Union[bool, Default] = _default,
        strict_slashes: Optional[Union[bool, Default]] = _default,
        with_registration: bool = True,
        with_ctx: bool = False,
    ):
        """Copy a blueprint instance with some optional parameters to override the values of attributes in the old instance.

        Args:
            name (str): Unique name of the blueprint.
            url_prefix (Optional[Union[str, Default]]): URL to be prefixed before all route URLs.
            version (Optional[Union[int, str, float, Default]]): Blueprint version.
            version_prefix (Union[str, Default]): The prefix of the version number shown in the URL.
            allow_route_overwrite (Union[bool, Default]): Whether to allow route overwrite or not.
            strict_slashes (Optional[Union[bool, Default]]): Enforce the API URLs are requested with a trailing "/*".
            with_registration (bool): Whether to register the new blueprint instance with Sanic apps that were registered with the old instance or not. Default is `True`.
            with_ctx (bool): Whether the ``ctx`` will be copied or not. Default is `False`.

        Returns:
            Blueprint: A new Blueprint instance with the specified attributes.
        """  # noqa: E501

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
        new_bp.copied_from = self.name

        if not isinstance(url_prefix, Default):
            new_bp.url_prefix = url_prefix
        if not isinstance(version, Default):
            new_bp.version = version
        if not isinstance(strict_slashes, Default):
            new_bp.strict_slashes = strict_slashes
        if not isinstance(version_prefix, Default):
            new_bp.version_prefix = version_prefix
        if not isinstance(allow_route_overwrite, Default):
            new_bp._allow_route_overwrite = allow_route_overwrite

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
        name_prefix: Optional[str] = "",
    ) -> BlueprintGroup:
        """Group multiple blueprints (or other blueprint groups) together.

        Gropuping blueprings is a method for modularizing and organizing
        your application's code. This can be a powerful tool for creating
        reusable components, logically structuring your application code,
        and easily maintaining route definitions in bulk.

        This is the preferred way to group multiple blueprints together.

        Args:
            blueprints (Union[Blueprint, BlueprintGroup]): Blueprints to be
                registered as a group.
            url_prefix (Optional[str]): URL route to be prepended to all
                sub-prefixes. Default is `None`.
            version (Optional[Union[int, str, float]]): API Version to be
                used for Blueprint group. Default is `None`.
            strict_slashes (Optional[bool]): Indicate strict slash
                termination behavior for URL. Default is `None`.
            version_prefix (str): Prefix to be used for the version in the
                URL. Default is "/v".
            name_prefix (Optional[str]): Prefix to be used for the name of
                the blueprints in the group. Default is an empty string.

        Returns:
            BlueprintGroup: A group of blueprints.

        Example:
            The resulting group will have the URL prefixes
            `'/v2/bp1'` and `'/v2/bp2'` for bp1 and bp2, respectively.
            ```python
            bp1 = Blueprint('bp1', url_prefix='/bp1')
            bp2 = Blueprint('bp2', url_prefix='/bp2')
            group = group(bp1, bp2, version=2)
            ```
        """

        def chain(nested) -> Iterable[Blueprint]:
            """Iterate through nested blueprints"""
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
            name_prefix=name_prefix,
        )
        for bp in chain(blueprints):
            bps.append(bp)
        return bps

    def register(self, app, options):
        """Register the blueprint to the sanic app.

        Args:
            app (Sanic): Sanic app to register the blueprint to.
            options (dict): Options to be passed to the blueprint.
        """

        self._apps.add(app)
        url_prefix = options.get("url_prefix", self.url_prefix)
        opt_version = options.get("version", None)
        opt_strict_slashes = options.get("strict_slashes", None)
        opt_version_prefix = options.get("version_prefix", self.version_prefix)
        opt_name_prefix = options.get("name_prefix", None)
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
            # Prepend the blueprint URI prefix if available
            uri = self._setup_uri(future.uri, url_prefix)

            route_error_format = (
                future.error_format if future.error_format else error_format
            )

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

            name = future.name
            if opt_name_prefix:
                name = f"{opt_name_prefix}_{future.name}"
            name = app.generate_name(name)
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
                route_error_format,
                future.route_context,
            )

            if (self, apply_route) in app._future_registry:
                continue

            registered.add(apply_route)
            route = app._apply_route(
                apply_route, overwrite=self._allow_route_overwrite
            )

            # If it is a copied BP, then make sure all of the names of routes
            # matchup with the new BP name
            if self.copied_from:
                for r in route:
                    r.name = r.name.replace(self.copied_from, self.name)
                    r.extra.ident = r.extra.ident.replace(
                        self.copied_from, self.name
                    )

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
            app._apply_signal(
                FutureSignal(
                    future.handler,
                    future.event,
                    future.condition,
                    False,
                    future.priority,
                )
            )

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

        if self._future_commands:
            raise SanicException(
                "Registering commands with blueprints is not supported."
            )

    async def dispatch(self, *args, **kwargs):
        """Dispatch a signal event

        Args:
            *args: Arguments to be passed to the signal event.
            **kwargs: Keyword arguments to be passed to the signal event.
        """
        condition = kwargs.pop("condition", {})
        condition.update({"__blueprint__": self.name})
        kwargs["condition"] = condition
        return await asyncio.gather(
            *[app.dispatch(*args, **kwargs) for app in self.apps]
        )

    def event(
        self,
        event: str,
        timeout: Optional[Union[int, float]] = None,
        *,
        condition: Optional[dict[str, Any]] = None,
    ):
        """Wait for a signal event to be dispatched.

        Args:
            event (str): Name of the signal event.
            timeout (Optional[Union[int, float]]): Timeout for the event to be
                dispatched.
            condition: If provided, method will only return when the signal
                is dispatched with the given condition.

        Returns:
            Awaitable: Awaitable for the event to be dispatched.
        """
        if condition is None:
            condition = {}
        condition.update({"__blueprint__": self.name})

        waiters = []
        for app in self.apps:
            waiter = app.signal_router.get_waiter(
                event, condition, exclusive=False
            )
            if not waiter:
                raise NotFound("Could not find signal %s" % event)
            waiters.append(waiter)

        return self._event(waiters, timeout)

    async def _event(self, waiters, timeout):
        done, pending = await asyncio.wait(
            [asyncio.create_task(waiter.wait()) for waiter in waiters],
            return_when=asyncio.FIRST_COMPLETED,
            timeout=timeout,
        )
        for task in pending:
            task.cancel()
        if not done:
            raise TimeoutError()
        (finished_task,) = done
        return finished_task.result()

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
        apps: set[Sanic], bp: Blueprint, futures: Sequence[tuple[Any, ...]]
    ):
        """Register futures to the apps.

        Args:
            apps (Set[Sanic]): Set of apps to register the futures to.
            bp (Blueprint): Blueprint that the futures belong to.
            futures (Sequence[Tuple[Any, ...]]): Sequence of futures to be
                registered.
        """

        for app in apps:
            app._future_registry.update({(bp, item) for item in futures})


bpg_base = MutableSequence[Blueprint]


class BlueprintGroup(bpg_base):
    """This class provides a mechanism to implement a Blueprint Group.

    The `BlueprintGroup` class allows grouping blueprints under a common
    URL prefix, version, and other shared attributes. It integrates with
    Sanic's Blueprint system, offering a custom iterator to treat an
    object of this class as a list/tuple.

    Although possible to instantiate a group directly, it is recommended
    to use the `Blueprint.group` method to create a group of blueprints.

    Args:
        url_prefix (Optional[str]): URL to be prefixed before all the
            Blueprint Prefixes. Default is `None`.
        version (Optional[Union[int, str, float]]): API Version for the
            blueprint group, inherited by each Blueprint. Default is `None`.
        strict_slashes (Optional[bool]): URL Strict slash behavior
            indicator. Default is `None`.
        version_prefix (str): Prefix for the version in the URL.
            Default is `"/v"`.
        name_prefix (Optional[str]): Prefix for the name of the blueprints
            in the group. Default is an empty string.

    Examples:
        ```python
        bp1 = Blueprint("bp1", url_prefix="/bp1")
        bp2 = Blueprint("bp2", url_prefix="/bp2")

        bp3 = Blueprint("bp3", url_prefix="/bp4")
        bp4 = Blueprint("bp3", url_prefix="/bp4")


        group1 = Blueprint.group(bp1, bp2)
        group2 = Blueprint.group(bp3, bp4, version_prefix="/api/v", version="1")


        @bp1.on_request
        async def bp1_only_middleware(request):
            print("applied on Blueprint : bp1 Only")


        @bp1.route("/")
        async def bp1_route(request):
            return text("bp1")


        @bp2.route("/<param>")
        async def bp2_route(request, param):
            return text(param)


        @bp3.route("/")
        async def bp3_route(request):
            return text("bp3")


        @bp4.route("/<param>")
        async def bp4_route(request, param):
            return text(param)


        @group1.on_request
        async def group_middleware(request):
            print("common middleware applied for both bp1 and bp2")


        # Register Blueprint group under the app
        app.blueprint(group1)
        app.blueprint(group2)
        ```
    """  # noqa: E501

    __slots__ = (
        "_blueprints",
        "_url_prefix",
        "_version",
        "_strict_slashes",
        "_version_prefix",
        "_name_prefix",
    )

    def __init__(
        self,
        url_prefix: Optional[str] = None,
        version: Optional[Union[int, str, float]] = None,
        strict_slashes: Optional[bool] = None,
        version_prefix: str = "/v",
        name_prefix: Optional[str] = "",
    ):
        self._blueprints: list[Blueprint] = []
        self._url_prefix = url_prefix
        self._version = version
        self._version_prefix = version_prefix
        self._strict_slashes = strict_slashes
        self._name_prefix = name_prefix

    @property
    def url_prefix(self) -> Optional[Union[int, str, float]]:
        """The URL prefix for the Blueprint Group.

        Returns:
            Optional[Union[int, str, float]]: URL prefix for the Blueprint
                Group.
        """
        return self._url_prefix

    @property
    def blueprints(self) -> list[Blueprint]:
        """A list of all the available blueprints under this group.

        Returns:
            List[Blueprint]: List of all the available blueprints under
                this group.
        """
        return self._blueprints

    @property
    def version(self) -> Optional[Union[str, int, float]]:
        """API Version for the Blueprint Group, if any.

        Returns:
            Optional[Union[str, int, float]]: API Version for the Blueprint
        """
        return self._version

    @property
    def strict_slashes(self) -> Optional[bool]:
        """Whether to enforce strict slashes for the Blueprint Group.

        Returns:
            Optional[bool]: Whether to enforce strict slashes for the
        """
        return self._strict_slashes

    @property
    def version_prefix(self) -> str:
        """Version prefix for the Blueprint Group.

        Returns:
            str: Version prefix for the Blueprint Group.
        """
        return self._version_prefix

    @property
    def name_prefix(self) -> Optional[str]:
        """Name prefix for the Blueprint Group.

        This is mainly needed when blueprints are copied in order to
        avoid name conflicts.

        Returns:
            Optional[str]: Name prefix for the Blueprint Group.
        """
        return self._name_prefix

    def __iter__(self) -> Iterator[Blueprint]:
        """Iterate over the list of blueprints in the group.

        Returns:
            Iterator[Blueprint]: Iterator for the list of blueprints in
        """
        return iter(self._blueprints)

    @overload
    def __getitem__(self, item: int) -> Blueprint: ...

    @overload
    def __getitem__(self, item: slice) -> MutableSequence[Blueprint]: ...

    def __getitem__(
        self, item: Union[int, slice]
    ) -> Union[Blueprint, MutableSequence[Blueprint]]:
        """Get the Blueprint object at the specified index.

        This method returns a blueprint inside the group specified by
        an index value. This will enable indexing, splice and slicing
        of the blueprint group like we can do with regular list/tuple.

        This method is provided to ensure backward compatibility with
        any of the pre-existing usage that might break.

        Returns:
            Blueprint: Blueprint object at the specified index.

        Raises:
            IndexError: If the index is out of range.
        """
        return self._blueprints[item]

    @overload
    def __setitem__(self, index: int, item: Blueprint) -> None: ...

    @overload
    def __setitem__(self, index: slice, item: Iterable[Blueprint]) -> None: ...

    def __setitem__(
        self,
        index: Union[int, slice],
        item: Union[Blueprint, Iterable[Blueprint]],
    ) -> None:
        """Set the Blueprint object at the specified index.

        Abstract method implemented to turn the `BlueprintGroup` class
        into a list like object to support all the existing behavior.

        This method is used to perform the list's indexed setter operation.

        Args:
            index (int): Index to use for removing a new Blueprint item
            item (Blueprint): New `Blueprint` object.

        Returns:
            None

        Raises:
            IndexError: If the index is out of range.
        """
        if isinstance(index, int):
            if not isinstance(item, Blueprint):
                raise TypeError("Expected a Blueprint instance")
            self._blueprints[index] = item
        elif isinstance(index, slice):
            if not isinstance(item, Iterable):
                raise TypeError("Expected an iterable of Blueprint instances")
            self._blueprints[index] = list(item)
        else:
            raise TypeError("Index must be int or slice")

    @overload
    def __delitem__(self, index: int) -> None: ...

    @overload
    def __delitem__(self, index: slice) -> None: ...

    def __delitem__(self, index: Union[int, slice]) -> None:
        """Delete the Blueprint object at the specified index.

        Abstract method implemented to turn the `BlueprintGroup` class
        into a list like object to support all the existing behavior.

        This method is used to delete an item from the list of blueprint
        groups like it can be done on a regular list with index.

        Args:
            index (int): Index to use for removing a new Blueprint item

        Returns:
            None

        Raises:
            IndexError: If the index is out of range.
        """
        del self._blueprints[index]

    def __len__(self) -> int:
        """Get the Length of the blueprint group object.

        Returns:
            int: Length of the blueprint group object.
        """
        return len(self._blueprints)

    def append(self, value: Blueprint) -> None:
        """Add a new Blueprint object to the group.

        The Abstract class `MutableSequence` leverages this append method to
        perform the `BlueprintGroup.append` operation.

        Args:
            value (Blueprint): New `Blueprint` object.

        Returns:
            None
        """
        self._blueprints.append(value)

    def exception(self, *exceptions: Exception, **kwargs) -> Callable:
        """Decorate a function to handle exceptions for all blueprints in the group.

        In case of nested Blueprint Groups, the same handler is applied
        across each of the Blueprints recursively.

        Args:
            *exceptions (Exception): Exceptions to handle
            **kwargs (dict): Optional Keyword arg to use with Middleware

        Returns:
            Partial function to apply the middleware

        Examples:
            ```python
            bp1 = Blueprint("bp1", url_prefix="/bp1")
            bp2 = Blueprint("bp2", url_prefix="/bp2")
            group1 = Blueprint.group(bp1, bp2)

            @group1.exception(Exception)
            def handler(request, exception):
                return text("Exception caught")
            ```
        """  # noqa: E501

        def register_exception_handler_for_blueprints(fn):
            for blueprint in self.blueprints:
                blueprint.exception(*exceptions, **kwargs)(fn)

        return register_exception_handler_for_blueprints

    def insert(self, index: int, item: Blueprint) -> None:
        """Insert a new Blueprint object to the group at the specified index.

        The Abstract class `MutableSequence` leverages this insert method to
        perform the `BlueprintGroup.append` operation.

        Args:
            index (int): Index to use for removing a new Blueprint item
            item (Blueprint): New `Blueprint` object.

        Returns:
            None
        """
        self._blueprints.insert(index, item)

    def middleware(self, *args, **kwargs):
        """A decorator that can be used to implement a Middleware for all blueprints in the group.

        In case of nested Blueprint Groups, the same middleware is applied
        across each of the Blueprints recursively.

        Args:
            *args (Optional): Optional positional Parameters to be use middleware
            **kwargs (Optional): Optional Keyword arg to use with Middleware

        Returns:
            Partial function to apply the middleware
        """  # noqa: E501

        def register_middleware_for_blueprints(fn):
            for blueprint in self.blueprints:
                blueprint.middleware(fn, *args, **kwargs)

        if args and callable(args[0]):
            fn = args[0]
            args = list(args)[1:]
            return register_middleware_for_blueprints(fn)
        return register_middleware_for_blueprints

    def on_request(self, middleware=None):
        """Convenience method to register a request middleware for all blueprints in the group.

        Args:
            middleware (Optional): Optional positional Parameters to be use middleware

        Returns:
            Partial function to apply the middleware
        """  # noqa: E501
        if callable(middleware):
            return self.middleware(middleware, "request")
        else:
            return partial(self.middleware, attach_to="request")

    def on_response(self, middleware=None):
        """Convenience method to register a response middleware for all blueprints in the group.

        Args:
            middleware (Optional): Optional positional Parameters to be use middleware

        Returns:
            Partial function to apply the middleware
        """  # noqa: E501
        if callable(middleware):
            return self.middleware(middleware, "response")
        else:
            return partial(self.middleware, attach_to="response")
