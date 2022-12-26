import re

from typing import Any, Optional

from sanic.base.meta import SanicMeta
from sanic.exceptions import SanicException
from sanic.mixins.exceptions import ExceptionMixin
from sanic.mixins.listeners import ListenerMixin
from sanic.mixins.middleware import MiddlewareMixin
from sanic.mixins.routes import RouteMixin
from sanic.mixins.signals import SignalMixin


VALID_NAME = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_\-]*$")


class BaseSanic(
    RouteMixin,
    MiddlewareMixin,
    ListenerMixin,
    ExceptionMixin,
    SignalMixin,
    metaclass=SanicMeta,
):
    __slots__ = ("name",)

    def __init__(
        self, name: Optional[str] = None, *args: Any, **kwargs: Any
    ) -> None:
        class_name = self.__class__.__name__

        if name is None:
            raise SanicException(
                f"{class_name} instance cannot be unnamed. "
                "Please use Sanic(name='your_application_name') instead.",
            )

        if not VALID_NAME.match(name):
            raise SanicException(
                f"{class_name} instance named '{name}' uses an invalid "
                "format. Names must begin with a character and may only "
                "contain alphanumeric characters, _, or -."
            )

        self.name = name

        for base in BaseSanic.__bases__:
            base.__init__(self, *args, **kwargs)  # type: ignore

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} {self.name}>"

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(name="{self.name}")'

    def __setattr__(self, name: str, value: Any) -> None:
        try:
            super().__setattr__(name, value)
        except AttributeError as e:
            raise AttributeError(
                f"Setting variables on {self.__class__.__name__} instances is "
                "not allowed. You should change your "
                f"{self.__class__.__name__} instance to use "
                f"instance.ctx.{name} instead.",
            ) from e
