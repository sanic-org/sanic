from typing import Optional

from sanic.base.meta import SanicMeta


class BaseMixin(metaclass=SanicMeta):
    """Base class for some other mixins."""

    name: str
    strict_slashes: Optional[bool]

    def _generate_name(self, *objects, unique_route_name_generate=False, methods=None, uri=None) -> str:
        name = None
        _named_route = False

        for obj in objects:
            if obj:
                if isinstance(obj, str):
                    name = obj
                    _named_route = True
                    break

                try:
                    name = obj.name
                except AttributeError:
                    try:
                        name = obj.__name__
                    except AttributeError:
                        continue
                else:
                    break

        if not name:  # noqa
            raise ValueError("Could not generate a name for handler")

        if not name.startswith(f"{self.name}."):
            if unique_route_name_generate and not _named_route:
                if methods:
                    methods = "-".join(methods)
                    name = f"{name}_{methods}"
                if uri:
                    uri = uri.replace("/", "S")
                    name = f"{name}_{uri}"
            name = f"{self.name}.{name}"

        return name
