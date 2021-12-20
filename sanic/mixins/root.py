class SanicMeta(type):
    @classmethod
    def __prepare__(metaclass, name, bases, **kwds):
        cls = super().__prepare__(metaclass, name, bases, **kwds)
        cls["__slots__"] = ()
        return cls
