from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from enum import IntEnum, auto
from itertools import count
from typing import Deque, Union

from sanic.models.handler_types import MiddlewareType


class MiddlewareLocation(IntEnum):
    REQUEST = auto()
    RESPONSE = auto()


class Middleware:
    """Middleware object that is used to encapsulate middleware functions.

    This should generally not be instantiated directly, but rather through
    the `sanic.Sanic.middleware` decorator and its variants.

    Args:
        func (MiddlewareType): The middleware function to be called.
        location (MiddlewareLocation): The location of the middleware.
        priority (int): The priority of the middleware.
    """

    _counter = count()
    count: int

    __slots__ = ("func", "priority", "location", "definition")

    def __init__(
        self,
        func: MiddlewareType,
        location: MiddlewareLocation,
        priority: int = 0,
    ) -> None:
        self.func = func
        self.priority = priority
        self.location = location
        self.definition = next(Middleware._counter)

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __hash__(self) -> int:
        return hash(self.func)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"func=<function {self.func.__name__}>, "
            f"priority={self.priority}, "
            f"location={self.location.name})"
        )

    @property
    def order(self) -> tuple[int, int]:
        """Return a tuple of the priority and definition order.

        This is used to sort the middleware.

        Returns:
            tuple[int, int]: The priority and definition order.
        """
        return (self.priority, -self.definition)

    @classmethod
    def convert(
        cls,
        *middleware_collections: Sequence[Union[Middleware, MiddlewareType]],
        location: MiddlewareLocation,
    ) -> Deque[Middleware]:
        """Convert middleware collections to a deque of Middleware objects.

        Args:
            *middleware_collections (Sequence[Union[Middleware, MiddlewareType]]):
                The middleware collections to convert.
            location (MiddlewareLocation): The location of the middleware.

        Returns:
            Deque[Middleware]: The converted middleware.
        """  # noqa: E501
        return deque(
            [
                middleware
                if isinstance(middleware, Middleware)
                else Middleware(middleware, location)
                for collection in middleware_collections
                for middleware in collection
            ]
        )

    @classmethod
    def reset_count(cls) -> None:
        """Reset the counter for the middleware definition order.

        This is used for testing.

        Returns:
            None
        """
        cls._counter = count()
        cls.count = next(cls._counter)
