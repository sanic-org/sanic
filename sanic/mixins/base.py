class Base(type):
    def __new__(cls, name, bases, attrs):
        init = attrs.get("__init__")

        def __init__(self, *args, **kwargs):
            nonlocal init
            for base in type(self).__bases__:
                if base.__name__ != "BaseMixin":
                    base.__init__(self, *args, **kwargs)

            if init:
                init(self, *args, **kwargs)

        attrs["__init__"] = __init__
        return type.__new__(cls, name, bases, attrs)


class BaseMixin(metaclass=Base):
    ...
