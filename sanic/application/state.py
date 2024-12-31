from __future__ import annotations

import logging

from dataclasses import dataclass, field
from pathlib import Path
from socket import socket
from ssl import SSLContext
from typing import TYPE_CHECKING, Any, Optional, Union

from sanic.application.constants import Mode, Server, ServerStage
from sanic.log import VerbosityFilter, logger
from sanic.server.async_server import AsyncioServer


if TYPE_CHECKING:
    from sanic import Sanic


@dataclass
class ApplicationServerInfo:
    """Information about a server instance."""

    settings: dict[str, Any]
    stage: ServerStage = field(default=ServerStage.STOPPED)
    server: Optional[AsyncioServer] = field(default=None)


@dataclass
class ApplicationState:
    """Application state.

    This class is used to store the state of the application. It is
    instantiated by the application and is available as `app.state`.
    """

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
    reload_dirs: set[Path] = field(default_factory=set)
    auto_reload: bool = field(default=False)
    server: Server = field(default=Server.SANIC)
    is_running: bool = field(default=False)
    is_started: bool = field(default=False)
    is_stopping: bool = field(default=False)
    verbosity: int = field(default=0)
    workers: int = field(default=0)
    primary: bool = field(default=True)
    server_info: list[ApplicationServerInfo] = field(default_factory=list)

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

    def set_verbosity(self, value: int) -> None:
        """Set the verbosity level.

        Args:
            value (int): Verbosity level.
        """
        VerbosityFilter.verbosity = value

    @property
    def is_debug(self) -> bool:
        """Check if the application is in debug mode.

        Returns:
            bool: `True` if the application is in debug mode, `False`
                otherwise.
        """
        return self.mode is Mode.DEBUG

    @property
    def stage(self) -> ServerStage:
        """Get the server stage.

        Returns:
            ServerStage: Server stage.
        """
        if not self.server_info:
            return ServerStage.STOPPED

        if all(info.stage is ServerStage.SERVING for info in self.server_info):
            return ServerStage.SERVING
        elif any(
            info.stage is ServerStage.SERVING for info in self.server_info
        ):
            return ServerStage.PARTIAL

        return ServerStage.STOPPED
