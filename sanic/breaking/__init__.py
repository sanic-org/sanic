from sanic.__version__ import __compatibility__

if __compatibility__ == "22.12":
    from .v22_12.request import (
        File,
        Request,
        RequestParameters,
        parse_multipart_form,
    )
elif __compatibility__ == "23.3":
    from .v23_3.request import (
        File,
        Request,
        RequestParameters,
        parse_multipart_form,
    )
else:
    raise RuntimeError(f"Unknown compatibility value: {__compatibility__}")
