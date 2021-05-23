from abc import ABC, abstractmethod
from typing import List, Set, Type


class BaseScheme(ABC):
    ident: str
    _registry: Set[Type] = set()

    def __init__(self, app) -> None:
        self.app = app

    @abstractmethod
    def run(self, directive: str, offset: int) -> None:
        ...

    def __init_subclass__(cls):
        BaseScheme._registry.add(cls)

    @property
    def trigger(self):
        return f"# {self.ident}: "

    def __call__(self, lines: List[str]) -> List[str]:
        self.output: List[str] = []

        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith(self.trigger):
                offset = len(line) - len(stripped)
                line = line.replace("  # noqa", "")
                _, directive = line.split(self.trigger, 1)
                self.run(directive, offset)
            else:
                self.add_line(line)

        return self.output

    def add_line(self, line: str) -> None:
        self.output.append(line)
