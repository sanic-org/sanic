from enum import Enum, IntEnum, auto


class StrEnum(str, Enum):  # no cov
    def _generate_next_value_(name: str, *args) -> str:  # type: ignore
        return name.lower()

    def __eq__(self, value: object) -> bool:
        value = str(value).upper()
        return super().__eq__(value)

    def __hash__(self) -> int:
        return hash(self.value)

    def __str__(self) -> str:
        return self.value


class Server(StrEnum):
    SANIC = auto()
    ASGI = auto()


class Mode(StrEnum):
    PRODUCTION = auto()
    DEBUG = auto()


class ServerStage(IntEnum):
    STOPPED = auto()
    PARTIAL = auto()
    SERVING = auto()
