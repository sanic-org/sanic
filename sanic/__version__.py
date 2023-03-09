__version__ = "23.3.0"
__compatibility__ = "22.12"

from inspect import currentframe, stack

for frame_info in stack():
    if frame_info.frame is not currentframe():
        value = frame_info.frame.f_globals.get("__SANIC_COMPATIBILITY__")
        if value:
            __compatibility__ = value
