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
FutureMiddleware = namedtuple("FutureMiddleware", ["middleware", "attach_to"])
FutureException = namedtuple("FutureException", ["handler", "args", "kwargs"])
FutureStatic = namedtuple(
    "FutureStatic",
    [
        "uri",
        "file_or_directory",
        "pattern",
        "use_modified_since",
        "use_content_range",
        "stream_large_files",
        "name",
        "host",
        "strict_slashes",
        "content_type",
    ],
)
