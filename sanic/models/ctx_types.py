from typing import Any, NamedTuple, Optional


class REPLLocal(NamedTuple):
    var: Any
    name: str
    desc: str


class REPLContext:
    def __init__(self):
        self._locals: set[REPLLocal] = set()

    def add_local(
        self,
        var: Any,
        name: Optional[str] = None,
        desc: Optional[str] = None,
    ):
        if name is None:
            name = var.__name__

        if desc is None:
            desc = var.__doc__

        desc = self._truncate(desc)

        self._locals.add(REPLLocal(var, name, desc))

    def __iter__(self):
        return iter(self._locals)

    @staticmethod
    def _truncate(s: str, limit: int = 40) -> str:
        return s[:limit] + "..." if len(s) > limit else s
