from enum import IntEnum, auto

from sanic.compat import UpperStrEnum


class RestartOrder(UpperStrEnum):
    SHUTDOWN_FIRST = auto()
    STARTUP_FIRST = auto()


class ProcessState(IntEnum):
    IDLE = auto()
    RESTARTING = auto()
    STARTING = auto()
    STARTED = auto()
    ACKED = auto()
    JOINED = auto()
    TERMINATED = auto()
