from sanic.base.meta import SanicMeta
from sanic.exceptions import SanicException

from .service import TouchUp


class TouchUpMeta(SanicMeta):
    def __new__(cls, name, bases, attrs, **kwargs):
        gen_class = super().__new__(cls, name, bases, attrs, **kwargs)

        methods = attrs.get("__touchup__")
        attrs["__touched__"] = False
        if methods:

            for method in methods:
                if method not in attrs:
                    raise SanicException(
                        "Cannot perform touchup on non-existent method: "
                        f"{name}.{method}"
                    )
                TouchUp.register(gen_class, method)

        return gen_class
