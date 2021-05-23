from inspect import getmembers, getmodule, getsource
from textwrap import dedent
from typing import Any, Dict, Set, Tuple, Type

from .schemes import BaseScheme


class TouchUp:
    _registry: Set[Tuple[Type, str]] = set()

    @classmethod
    def run(cls, app):
        for target, method_name in cls._registry:
            method = getattr(target, method_name)
            module = getmodule(target)
            module_globals = dict(getmembers(module))

            raw_source = getsource(method)
            src = dedent(raw_source)
            lines = src.splitlines()

            for scheme in BaseScheme._registry:
                handler = scheme(app)
                lines = handler(lines)

            joined = "\n".join(lines)

            compiled_src = compile(joined, "", "exec")
            exec_locals: Dict[str, Any] = {}
            exec(compiled_src, module_globals, exec_locals)
            setattr(target, method_name, exec_locals[method_name])

    @classmethod
    def register(cls, target, method_name):
        cls._registry.add((target, method_name))
