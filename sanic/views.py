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


if TYPE_CHECKING:  # no cov
    from sanic import Sanic
    from sanic.blueprints import Blueprint


class HTTPMethodView:
    """Simple class based implementation of view for the sanic.
    You should implement methods (get, post, put, patch, delete) for the class
    to every HTTP method you want to support.

    For example:

    .. code-block:: python

        class DummyView(HTTPMethodView):
            def get(self, request, *args, **kwargs):
                return text('I am get method')
            def put(self, request, *args, **kwargs):
                return text('I am put method')

    If someone tries to use a non-implemented method, there will be a
    405 response.

    If you need any url params just mention them in method definition:

    .. code-block:: python

        class DummyView(HTTPMethodView):
            def get(self, request, my_param_here, *args, **kwargs):
                return text('I am get method with %s' % my_param_here)

    To add the view into the routing you could use

        1) ``app.add_route(DummyView.as_view(), '/')``, OR
        2) ``app.route('/')(DummyView.as_view())``

    To add any decorator you could set it into decorators variable
    """

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

    def dispatch_request(self, request, *args, **kwargs):
        handler = getattr(self, request.method.lower(), None)
        if not handler and request.method == "HEAD":
            handler = self.get
        return handler(request, *args, **kwargs)

    @classmethod
    def as_view(cls, *class_args: Any, **class_kwargs: Any) -> RouteHandler:
        """Return view function for use with the routing system, that
        dispatches request to appropriate handler method.
        """

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
    func.is_stream = True
    return func
