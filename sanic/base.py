from sanic.mixins.exceptions import ExceptionMixin
from sanic.mixins.listeners import ListenerMixin
from sanic.mixins.middleware import MiddlewareMixin
from sanic.mixins.routes import RouteMixin


class Base(type):
    def __new__(cls, name, bases, attrs):
        init = attrs.get("__init__")

        def __init__(self, *args, **kwargs):
            nonlocal init
            nonlocal name

            bases = [
                b for base in type(self).__bases__ for b in base.__bases__
            ]

            for base in bases:
                base.__init__(self, *args, **kwargs)

            if init:
                init(self, *args, **kwargs)

        attrs["__init__"] = __init__
        return type.__new__(cls, name, bases, attrs)


class BaseSanic(
    RouteMixin,
    MiddlewareMixin,
    ListenerMixin,
    ExceptionMixin,
    metaclass=Base,
):
    def __str__(self) -> str:
        return f"<{self.__class__.__name__} {self.name}>"

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(name="{self.name}")'
