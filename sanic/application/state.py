from __future__ import annotations

import logging

from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto
from typing import TYPE_CHECKING, Any, Union

from sanic.log import logger


if TYPE_CHECKING:
    from sanic import Sanic


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


class Stage(IntEnum):
    INIT = auto()
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()


@dataclass
class ApplicationState:
    app: Sanic
    host: str = field(default="")
    mode: Mode = field(default=Mode.PRODUCTION)
    port: int = field(default=0)
    server: Server = field(default=Server.SANIC)
    stage: Stage = field(default=Stage.INIT)
    verbosity: int = field(default=0)

    # This property relates to the ApplicationState instance and should
    # not be changed except in the __post_init__ method
    _init: bool = field(default=False)

    def __post_init__(self) -> None:
        self._init = True

    def __setattr__(self, name: str, value: Any) -> None:
        if self._init and name == "_init":
            raise RuntimeError(
                "Cannot change the value of _init after instantiation"
            )
        super().__setattr__(name, value)
        if self._init and hasattr(self, f"set_{name}"):
            getattr(self, f"set_{name}")(value)

    def set_mode(self, value: Union[str, Mode]):
        if hasattr(self.app, "error_handler"):
            self.app.error_handler.debug = self.app.debug
        if getattr(self.app, "configure_logging", False) and self.app.debug:
            logger.setLevel(logging.DEBUG)

    @property
    def is_debug(self):
        return self.mode is Mode.DEBUG

    @property
    def is_running(self):
        return self.stage is Stage.RUNNING
