from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterable,
    List,
    Optional,
    Union,
)

from sanic.models.handler_types import RouteHandler
from sanic.request.types import Request


if TYPE_CHECKING:
    from sanic import Sanic
    from sanic.blueprints import Blueprint


class HTTPMethodView:
    """Class based implementation for creating and grouping handlers

    Class-based views (CBVs) are an alternative to function-based views. They
    allow you to reuse common logic, and group related views, while keeping
    the flexibility of function-based views.


    To use a class-based view, subclass the method handler, and implement
    methods (`get`, `post`, `put`, `patch`, `delete`) for the class
    to correspond to each HTTP method you want to support.

    For example:

    ```python
    class DummyView(HTTPMethodView):
        def get(self, request: Request):
            return text('I am get method')

        def put(self, request: Request):
            return text('I am put method')
    ```

    If someone tries to use a non-implemented method, they will reveive a
    405 response.

    If you need any url params just include them in method signature, like
    you would for function-based views.

    ```python
    class DummyView(HTTPMethodView):
        def get(self, request: Request, my_param_here: str):
            return text(f"I am get method with {my_param_here}")
    ```

    Next, you need to attach the view to the app or blueprint. You can do this
    in the exact same way as you would for a function-based view, except you
    should you use `MyView.as_view()` instead of `my_view_handler`.

    ```python
    app.add_route(DummyView.as_view(), "/<my_param_here>")
    ```

    Alternatively, you can use the `attach` method:

    ```python
    DummyView.attach(app, "/<my_param_here>")
    ```

    Or, at the time of subclassing:

    ```python
    class DummyView(HTTPMethodView, attach=app, uri="/<my_param_here>"):
        ...
    ```

    To add a decorator, you can either:

    1. Add it to the `decorators` list on the class, which will apply it to
         all methods on the class; or
    2. Add it to the method directly, which will only apply it to that method.

    ```python
    class DummyView(HTTPMethodView):
        decorators = [my_decorator]
        ...

    # or

    class DummyView(HTTPMethodView):
        @my_decorator
        def get(self, request: Request):
            ...
    ```

    One catch is that you need to be mindful that the call inside the decorator
    may need to account for the `self` argument, which is passed to the method
    as the first argument. Alternatively, you may want to also mark your method
    as `staticmethod` to avoid this.

    Available attributes at the time of subclassing:
    - **attach** (Optional[Union[Sanic, Blueprint]]): The app or blueprint to
        attach the view to.
    - **uri** (str): The uri to attach the view to.
    - **methods** (Iterable[str]): The HTTP methods to attach the view to.
        Defaults to `{"GET"}`.
    - **host** (Optional[str]): The host to attach the view to.
    - **strict_slashes** (Optional[bool]): Whether to add a redirect rule for
        the uri with a trailing slash.
    - **version** (Optional[int]): The version to attach the view to.
    - **name** (Optional[str]): The name to attach the view to.
    - **stream** (bool): Whether the view is a stream handler.
    - **version_prefix** (str): The prefix to use for the version. Defaults
        to `"/v"`.
    """

    get: Optional[Callable[..., Any]]

    decorators: List[Callable[[Callable[..., Any]], Callable[..., Any]]] = []

    def __init_subclass__(
        cls,
        attach: Optional[Union[Sanic, Blueprint]] = None,
        uri: str = "",
        methods: Iterable[str] = frozenset({"GET"}),
        host: Optional[str] = None,
        strict_slashes: Optional[bool] = None,
        version: Optional[int] = None,
        name: Optional[str] = None,
        stream: bool = False,
        version_prefix: str = "/v",
    ) -> None:
        if attach:
            cls.attach(
                attach,
                uri=uri,
                methods=methods,
                host=host,
                strict_slashes=strict_slashes,
                version=version,
                name=name,
                stream=stream,
                version_prefix=version_prefix,
            )

    def dispatch_request(self, request: Request, *args, **kwargs):
        """Dispatch request to appropriate handler method."""
        handler = getattr(self, request.method.lower(), None)
        if not handler and request.method == "HEAD":
            handler = self.get
        if not handler:
            # The router will never allow us to get here, but this is
            # included as a fallback and for completeness.
            raise NotImplementedError(
                f"{request.method} is not supported for this endpoint."
            )
        return handler(request, *args, **kwargs)

    @classmethod
    def as_view(cls, *class_args: Any, **class_kwargs: Any) -> RouteHandler:
        """Return view function for use with the routing system, that dispatches request to appropriate handler method.

        If you need to pass arguments to the class's constructor, you can
        pass the arguments to `as_view` and they will be passed to the class
        `__init__` method.

        Args:
            *class_args: Variable length argument list for the class instantiation.
            **class_kwargs: Arbitrary keyword arguments for the class instantiation.

        Returns:
            RouteHandler: The view function.

        Examples:
            ```python
            class DummyView(HTTPMethodView):
                def __init__(self, foo: MyFoo):
                    self.foo = foo

                async def get(self, request: Request):
                    return text(self.foo.bar)

            app.add_route(DummyView.as_view(foo=MyFoo()), "/")
            ```
        """  # noqa: E501

        def view(*args, **kwargs):
            self = view.view_class(*class_args, **class_kwargs)
            return self.dispatch_request(*args, **kwargs)

        if cls.decorators:
            view.__module__ = cls.__module__
            for decorator in cls.decorators:
                view = decorator(view)

        view.view_class = cls  # type: ignore
        view.__doc__ = cls.__doc__
        view.__module__ = cls.__module__
        view.__name__ = cls.__name__
        return view

    @classmethod
    def attach(
        cls,
        to: Union[Sanic, Blueprint],
        uri: str,
        methods: Iterable[str] = frozenset({"GET"}),
        host: Optional[str] = None,
        strict_slashes: Optional[bool] = None,
        version: Optional[int] = None,
        name: Optional[str] = None,
        stream: bool = False,
        version_prefix: str = "/v",
    ) -> None:
        """Attaches the view to a Sanic app or Blueprint at the specified URI.

        Args:
            cls: The class that this method is part of.
            to (Union[Sanic, Blueprint]): The Sanic application or Blueprint to attach to.
            uri (str): The URI to bind the view to.
            methods (Iterable[str], optional): A collection of HTTP methods that the view should respond to. Defaults to `frozenset({"GET"})`.
            host (Optional[str], optional): A specific host or hosts to bind the view to. Defaults to `None`.
            strict_slashes (Optional[bool], optional): Enforce or not the trailing slash. Defaults to `None`.
            version (Optional[int], optional): Version of the API if versioning is used. Defaults to `None`.
            name (Optional[str], optional): Unique name for the route. Defaults to `None`.
            stream (bool, optional): Enable or disable streaming for the view. Defaults to `False`.
            version_prefix (str, optional): The prefix for the version, if versioning is used. Defaults to `"/v"`.
        """  # noqa: E501
        to.add_route(
            cls.as_view(),
            uri=uri,
            methods=methods,
            host=host,
            strict_slashes=strict_slashes,
            version=version,
            name=name,
            stream=stream,
            version_prefix=version_prefix,
        )


def stream(func):
    """Decorator to mark a function as a stream handler."""
    func.is_stream = True
    return func
