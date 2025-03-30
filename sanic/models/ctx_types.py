from typing import Any, NamedTuple, Optional


class REPLLocal(NamedTuple):
    var: Any
    name: str
    desc: str


class REPLContext:
    BUILTINS = {
        "app": "The Sanic application instance",
        "sanic": "The Sanic module",
        "do": "An async function to fake a request to the application",
        "client": "A client to access the Sanic app instance using httpx",
    }

    def __init__(self):
        self._locals: set[REPLLocal] = set()

    def add(
        self,
        var: Any,
        name: Optional[str] = None,
        desc: Optional[str] = None,
    ):
        """Add a local variable to be available in REPL context.

        Args:
            var (Any): A module, class, object or a class.
            name (Optional[str], optional): An alias for the local. Defaults to None.
            desc (Optional[str], optional): A brief description for the local. Defaults to None.
        """  # noqa: E501
        if name is None:
            try:
                name = var.__name__
            except AttributeError:
                name = var.__class__.__name__

        if desc is None:
            try:
                desc = var.__doc__ or ""
            except AttributeError:
                desc = str(type(var))

        assert isinstance(desc, str) and isinstance(
            name, str
        )  # Just to make mypy happy

        if name in self.BUILTINS:
            raise ValueError(f"Cannot override built-in variable: {name}")

        desc = self._truncate(desc)

        self._locals.add(REPLLocal(var, name, desc))

    def __setattr__(self, name: str, value: Any):
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self.add(value, name)

    def __iter__(self):
        return iter(self._locals)

    @staticmethod
    def _truncate(s: str, limit: int = 40) -> str:
        s = s.replace("\n", " ")
        return s[:limit] + "..." if len(s) > limit else s
