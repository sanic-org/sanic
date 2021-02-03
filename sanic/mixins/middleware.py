from functools import partial
from typing import List

from sanic.models.futures import FutureMiddleware


class MiddlewareMixin:
    def __init__(self, *args, **kwargs) -> None:
        self._future_middleware: List[FutureMiddleware] = list()

    def _apply_middleware(self, middleware: FutureMiddleware):
        raise NotImplementedError

    def middleware(
        self, middleware_or_request, attach_to="request", apply=True
    ):
        """
        Decorate and register middleware to be called before a request.
        Can either be called as *@app.middleware* or
        *@app.middleware('request')*

        :param: middleware_or_request: Optional parameter to use for
            identifying which type of middleware is being registered.
        """

        def register_middleware(middleware, attach_to="request"):
            nonlocal apply

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

    def on_request(self, middleware):
        return self.middleware(middleware, "request")

    def on_response(self, middleware):
        return self.middleware(middleware, "response")
