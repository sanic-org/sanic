from __future__ import annotations

from functools import wraps
from inspect import isawaitable
from typing import Callable, Optional, Union

from sanic.base.meta import SanicMeta
from sanic.models.futures import FutureCommand


class CommandMixin(metaclass=SanicMeta):
    def __init__(self, *args, **kwargs) -> None:
        self._future_commands: set[FutureCommand] = set()

    def command(
        self, maybe_func: Optional[Callable] = None, *, name: str = ""
    ) -> Union[Callable, Callable[[Callable], Callable]]:
        def decorator(f):
            @wraps(f)
            async def decorated_function(*args, **kwargs):
                response = f(*args, **kwargs)
                if isawaitable(response):
                    response = await response
                return response

            self._future_commands.add(
                FutureCommand(name or f.__name__, decorated_function)
            )
            return decorated_function

        return decorator(maybe_func) if maybe_func else decorator
