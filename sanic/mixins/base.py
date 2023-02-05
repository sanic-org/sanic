from typing import Optional

from sanic.base.meta import SanicMeta


class BaseMixin(metaclass=SanicMeta):
    name: str
    strict_slashes: Optional[bool]

    def _generate_name(self, *objects) -> str:
        name = None

        for obj in objects:
            if obj:
                if isinstance(obj, str):
                    name = obj
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
            name = f"{self.name}.{name}"

        return name
