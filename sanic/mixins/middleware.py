from collections import deque
from functools import partial
from operator import attrgetter
from typing import Callable, Union, overload

from sanic.base.meta import SanicMeta
from sanic.middleware import Middleware, MiddlewareLocation
from sanic.models.futures import FutureMiddleware, MiddlewareType
from sanic.router import Router


class MiddlewareMixin(metaclass=SanicMeta):
    router: Router

    def __init__(self, *args, **kwargs) -> None:
        self._future_middleware: list[FutureMiddleware] = []

    def _apply_middleware(self, middleware: FutureMiddleware):
        raise NotImplementedError  # noqa

    @overload
    def middleware(
        self,
        middleware_or_request: MiddlewareType,
        attach_to: str = "request",
        apply: bool = True,
        *,
        priority: int = 0,
    ) -> MiddlewareType: ...

    @overload
    def middleware(
        self,
        middleware_or_request: str,
        attach_to: str = "request",
        apply: bool = True,
        *,
        priority: int = 0,
    ) -> Callable[[MiddlewareType], MiddlewareType]: ...

    def middleware(
        self,
        middleware_or_request: Union[MiddlewareType, str],
        attach_to: str = "request",
        apply: bool = True,
        *,
        priority: int = 0,
    ) -> Union[MiddlewareType, Callable[[MiddlewareType], MiddlewareType]]:
        """Decorator for registering middleware.

        Decorate and register middleware to be called before a request is
        handled or after a response is created. Can either be called as
        *@app.middleware* or *@app.middleware('request')*. Although, it is
        recommended to use *@app.on_request* or *@app.on_response* instead
        for clarity and convenience.

        See [Middleware](/guide/basics/middleware) for more information.

        Args:
            middleware_or_request (Union[Callable, str]): Middleware function
                or the keyword 'request' or 'response'.
            attach_to (str, optional): When to apply the middleware;
                either 'request' (before the request is handled) or 'response'
                (after the response is created). Defaults to `'request'`.
            apply (bool, optional): Whether the middleware should be applied.
                Defaults to `True`.
            priority (int, optional): The priority level of the middleware.
                Lower numbers are executed first. Defaults to `0`.

        Returns:
            Union[Callable, Callable[[Callable], Callable]]: The decorated
                middleware function or a partial function depending on how
                the method was called.

        Example:
            ```python
            @app.middleware('request')
            async def custom_middleware(request):
                ...
            ```
        """

        def register_middleware(middleware, attach_to="request"):
            nonlocal apply

            location = (
                MiddlewareLocation.REQUEST
                if attach_to == "request"
                else MiddlewareLocation.RESPONSE
            )
            middleware = Middleware(middleware, location, priority=priority)
            future_middleware = FutureMiddleware(middleware, attach_to)
            self._future_middleware.append(future_middleware)
            if apply:
                self._apply_middleware(future_middleware)
            return middleware

        # Detect which way this was called, @middleware or @middleware('AT')
        if callable(middleware_or_request):
            return register_middleware(
                middleware_or_request, attach_to=attach_to
            )
        else:
            return partial(
                register_middleware, attach_to=middleware_or_request
            )

    def on_request(self, middleware=None, *, priority=0) -> MiddlewareType:
        """Register a middleware to be called before a request is handled.

        This is the same as *@app.middleware('request')*.

        Args:
            middleware (Callable, optional): A callable that takes in a
                request. Defaults to `None`.

        Returns:
            Callable: The decorated middleware function or a partial function
                depending on how the method was called.

        Examples:
            ```python
            @app.on_request
            async def custom_middleware(request):
                request.ctx.custom = 'value'
            ```
        """
        if callable(middleware):
            return self.middleware(middleware, "request", priority=priority)
        else:
            return partial(  # type: ignore
                self.middleware, attach_to="request", priority=priority
            )

    def on_response(self, middleware=None, *, priority=0):
        """Register a middleware to be called after a response is created.

        This is the same as *@app.middleware('response')*.

        Args:
            middleware (Callable, optional): A callable that takes in a
                request and response. Defaults to `None`.

        Returns:
            Callable: The decorated middleware function or a partial function
                depending on how the method was called.

        Examples:
            ```python
            @app.on_response
            async def custom_middleware(request, response):
                response.headers['X-Server'] = 'Sanic'
            ```
        """
        if callable(middleware):
            return self.middleware(middleware, "response", priority=priority)
        else:
            return partial(
                self.middleware, attach_to="response", priority=priority
            )

    def finalize_middleware(self) -> None:
        """Finalize the middleware configuration for the Sanic application.

        This method completes the middleware setup for the application.
        Middleware in Sanic is used to process requests globally before they
        reach individual routes or after routes have been processed.

        Finalization consists of identifying defined routes and optimizing
        Sanic's performance to meet the application's specific needs. If
        you are manually adding routes, after Sanic has started, you will
        typically want to use the `amend` context manager rather than
        calling this method directly.

        .. note::
            This method is usually called internally during the server setup
            process and does not typically need to be invoked manually.

        Example:
            ```python
            app.finalize_middleware()
            ```
        """
        for route in self.router.routes:
            request_middleware = Middleware.convert(
                self.request_middleware,  # type: ignore
                self.named_request_middleware.get(route.name, deque()),  # type: ignore  # noqa: E501
                location=MiddlewareLocation.REQUEST,
            )
            response_middleware = Middleware.convert(
                self.response_middleware,  # type: ignore
                self.named_response_middleware.get(route.name, deque()),  # type: ignore  # noqa: E501
                location=MiddlewareLocation.RESPONSE,
            )
            route.extra.request_middleware = deque(
                sorted(
                    request_middleware,
                    key=attrgetter("order"),
                    reverse=True,
                )
            )
            route.extra.response_middleware = deque(
                sorted(
                    response_middleware,
                    key=attrgetter("order"),
                    reverse=True,
                )[::-1]
            )
        request_middleware = Middleware.convert(
            self.request_middleware,  # type: ignore
            location=MiddlewareLocation.REQUEST,
        )
        response_middleware = Middleware.convert(
            self.response_middleware,  # type: ignore
            location=MiddlewareLocation.RESPONSE,
        )
        self.request_middleware = deque(
            sorted(
                request_middleware,
                key=attrgetter("order"),
                reverse=True,
            )
        )
        self.response_middleware = deque(
            sorted(
                response_middleware,
                key=attrgetter("order"),
                reverse=True,
            )[::-1]
        )
