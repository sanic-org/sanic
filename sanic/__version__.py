__version__ = "23.3.0"
__compatibility__ = "22.12"

from inspect import currentframe, stack

for frame_info in stack():
    if frame_info.frame is not currentframe():
        for member, value in frame_info.frame.f_globals.items():
            if member.startswith("__") and member.isupper():
                __compatibility__ = value
