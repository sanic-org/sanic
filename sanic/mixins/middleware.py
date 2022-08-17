from collections import deque
from functools import partial
from operator import attrgetter
from typing import List

from sanic.base.meta import SanicMeta
from sanic.middleware import Middleware, MiddlewareLocation
from sanic.models.futures import FutureMiddleware
from sanic.router import Router


class MiddlewareMixin(metaclass=SanicMeta):
    router: Router

    def __init__(self, *args, **kwargs) -> None:
        self._future_middleware: List[FutureMiddleware] = []

    def _apply_middleware(self, middleware: FutureMiddleware):
        raise NotImplementedError  # noqa

    def middleware(
        self,
        middleware_or_request,
        attach_to="request",
        apply=True,
        *,
        priority=0
    ):
        """
        Decorate and register middleware to be called before a request
        is handled or after a response is created. Can either be called as
        *@app.middleware* or *@app.middleware('request')*.

        `See user guide re: middleware
        <https://sanicframework.org/guide/basics/middleware.html>`__

        :param: middleware_or_request: Optional parameter to use for
            identifying which type of middleware is being registered.
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

    def on_request(self, middleware=None, *, priority=0):
        """Register a middleware to be called before a request is handled.

        This is the same as *@app.middleware('request')*.

        :param: middleware: A callable that takes in request.
        """
        if callable(middleware):
            return self.middleware(middleware, "request", priority=priority)
        else:
            return partial(
                self.middleware, attach_to="request", priority=priority
            )

    def on_response(self, middleware=None, *, priority=0):
        """Register a middleware to be called after a response is created.

        This is the same as *@app.middleware('response')*.

        :param: middleware:
            A callable that takes in a request and its response.
        """
        if callable(middleware):
            return self.middleware(middleware, "response", priority=priority)
        else:
            return partial(
                self.middleware, attach_to="response", priority=priority
            )

    def finalize_middleware(self):
        for route in self.router.routes:
            request_middleware = Middleware.convert(
                self.request_middleware,
                self.named_request_middleware.get(route.name, deque()),
                location=MiddlewareLocation.REQUEST,
            )
            response_middleware = Middleware.convert(
                self.response_middleware,
                self.named_response_middleware.get(route.name, deque()),
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
            self.request_middleware,
            location=MiddlewareLocation.REQUEST,
        )
        response_middleware = Middleware.convert(
            self.response_middleware,
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
