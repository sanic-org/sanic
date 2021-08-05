from inspect import getmembers, getmodule
from typing import Set, Tuple, Type

from .schemes import BaseScheme


class TouchUp:
    _registry: Set[Tuple[Type, str]] = set()

    @classmethod
    def run(cls, app):
        for target, method_name in cls._registry:
            method = getattr(target, method_name)

            if app.test_mode:
                placeholder = f"_{method_name}"
                if hasattr(target, placeholder):
                    method = getattr(target, placeholder)
                else:
                    setattr(target, placeholder, method)

            module = getmodule(target)
            module_globals = dict(getmembers(module))

            for scheme in BaseScheme._registry:
                modified = scheme(app)(method, module_globals)
                setattr(target, method_name, modified)

            target.__touched__ = True

    @classmethod
    def register(cls, target, method_name):
        cls._registry.add((target, method_name))
