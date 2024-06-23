from typing import Optional, Protocol, Union

from sanic.base.meta import SanicMeta


class NameProtocol(Protocol):
    name: str


class DunderNameProtocol(Protocol):
    __name__: str


class BaseMixin(metaclass=SanicMeta):
    """Base class for various mixins."""

    name: str
    strict_slashes: Optional[bool]

    def _generate_name(
        self, *objects: Union[NameProtocol, DunderNameProtocol, str]
    ) -> str:
        name: Optional[str] = None
        for obj in objects:
            if not obj:
                continue
            if isinstance(obj, str):
                name = obj
            else:
                name = getattr(obj, "name", getattr(obj, "__name__", None))

            if name:
                break
        if not name or not isinstance(name, str):
            raise ValueError("Could not generate a name for handler")

        if not name.startswith(f"{self.name}."):
            name = f"{self.name}.{name}"

        return name

    def generate_name(self, *objects) -> str:
        return self._generate_name(*objects)
