from typing import Optional

from sanic.base.meta import SanicMeta


class BaseMixin(metaclass=SanicMeta):
    """Base class for some other mixins."""

    name: str
    strict_slashes: Optional[bool]

    def _generate_name(self, *objects, route_generate=False, methods=None, uri=None) -> str:
        name = None
        named_route = False

        for obj in objects:
            if obj:
                if isinstance(obj, str):
                    name = obj
                    named_route = True
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
            if route_generate and not named_route:
                if methods:
                    methods = "_".join(methods)
                    name = f"{name}_{methods}"
                if uri:
                    # uri = uri.replace("/", "/")
                    name = f"{name}_{uri}"
            name = f"{self.name}.{name}"

        return name
