from abc import ABC, abstractmethod
from ast import NodeTransformer, parse
from inspect import getsource
from textwrap import dedent
from typing import Any, Dict, List, Set, Type


class BaseScheme(ABC):
    ident: str
    _registry: Set[Type] = set()

    def __init__(self, app) -> None:
        self.app = app

    @abstractmethod
    def visitors(self) -> List[NodeTransformer]:
        ...

    def __init_subclass__(cls):
        BaseScheme._registry.add(cls)

    def __call__(self):
        return self.visitors()

    @classmethod
    def build(cls, method, module_globals, app):
        raw_source = getsource(method)
        src = dedent(raw_source)
        node = parse(src)

        for scheme in cls._registry:
            for visitor in scheme(app)():
                node = visitor.visit(node)

        compiled_src = compile(node, method.__name__, "exec")
        exec_locals: Dict[str, Any] = {}
        exec(compiled_src, module_globals, exec_locals)  # nosec
        return exec_locals[method.__name__]
