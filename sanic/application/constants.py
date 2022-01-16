from enum import Enum, IntEnum, auto


class StrEnum(str, Enum):
    def _generate_next_value_(name: str, *args) -> str:  # type: ignore
        return name.lower()


class Server(StrEnum):
    SANIC = auto()
    ASGI = auto()
    GUNICORN = auto()


class Mode(StrEnum):
    PRODUCTION = auto()
    DEBUG = auto()


class ServerStage(IntEnum):
    STOPPED = auto()
    PARTIAL = auto()
    SERVING = auto()
