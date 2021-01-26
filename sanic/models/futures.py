from collections import namedtuple


FutureRoute = namedtuple(
    "FutureRoute",
    [
        "handler",
        "uri",
        "methods",
        "host",
        "strict_slashes",
        "stream",
        "version",
        "name",
        "ignore_body",
    ],
)
FutureListener = namedtuple(
    "FutureListener", ["handler", "uri", "methods", "host"]
)
FutureMiddleware = namedtuple(
    "FutureMiddleware", ["middleware", "args", "kwargs"]
)
FutureException = namedtuple("FutureException", ["handler", "args", "kwargs"])
FutureStatic = namedtuple(
    "FutureStatic", ["uri", "file_or_directory", "args", "kwargs"]
)
