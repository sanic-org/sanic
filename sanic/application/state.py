from __future__ import annotations

import logging

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from socket import socket
from ssl import SSLContext
from typing import TYPE_CHECKING, Any, Optional, Set, Union

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


@dataclass
class ApplicationState:
    app: Sanic
    asgi: bool = field(default=False)
    coffee: bool = field(default=False)
    fast: bool = field(default=False)
    host: str = field(default="")
    port: int = field(default=0)
    ssl: Optional[SSLContext] = field(default=None)
    sock: Optional[socket] = field(default=None)
    unix: Optional[str] = field(default=None)
    mode: Mode = field(default=Mode.PRODUCTION)
    reload_dirs: Set[Path] = field(default_factory=set)
    server: Server = field(default=Server.SANIC)
    is_running: bool = field(default=False)
    is_started: bool = field(default=False)
    is_stopping: bool = field(default=False)
    verbosity: int = field(default=0)
    workers: int = field(default=0)

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
