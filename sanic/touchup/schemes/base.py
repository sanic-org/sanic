from abc import ABC, abstractmethod
from typing import Set, Type


class BaseScheme(ABC):
    ident: str
    _registry: Set[Type] = set()

    def __init__(self, app) -> None:
        self.app = app

    @abstractmethod
    def run(self, method, module_globals) -> None:
        ...

    def __init_subclass__(cls):
        BaseScheme._registry.add(cls)

    def __call__(self, method, module_globals):
        return self.run(method, module_globals)
