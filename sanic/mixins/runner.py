from __future__ import annotations

import os
import platform
import sys

from asyncio import (
    AbstractEventLoop,
    CancelledError,
    Protocol,
    all_tasks,
    get_event_loop,
    get_running_loop,
    new_event_loop,
)
from contextlib import suppress
from functools import partial
from importlib import import_module
from pathlib import Path
from socket import socket
from ssl import SSLContext
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Type, Union

from sanic import reloader_helpers
from sanic.application.logo import get_logo
from sanic.application.motd import MOTD
from sanic.application.state import ApplicationServerInfo, Mode, ServerStage
from sanic.base.meta import SanicMeta
from sanic.compat import OS_IS_WINDOWS
from sanic.helpers import _default
from sanic.log import Colors, error_logger, logger
from sanic.models.handler_types import ListenerType
from sanic.server import Signal as ServerSignal
from sanic.server import try_use_uvloop
from sanic.server.async_server import AsyncioServer
from sanic.server.events import trigger_events
from sanic.server.protocols.http_protocol import HttpProtocol
from sanic.server.protocols.websocket_protocol import WebSocketProtocol
from sanic.server.runners import serve, serve_multiple, serve_single
from sanic.tls import process_to_context


if TYPE_CHECKING:  # no cov
    from sanic import Sanic
    from sanic.application.state import ApplicationState
    from sanic.config import Config

SANIC_PACKAGES = ("sanic-routing", "sanic-testing", "sanic-ext")


class RunnerMixin(metaclass=SanicMeta):
    _app_registry: Dict[str, Sanic]
    config: Config
    listeners: Dict[str, List[ListenerType[Any]]]
    state: ApplicationState
    websocket_enabled: bool

    def make_coffee(self, *args, **kwargs):
        self.state.coffee = True
        self.run(*args, **kwargs)

    def run(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        *,
        dev: bool = False,
        debug: bool = False,
        auto_reload: Optional[bool] = None,
        ssl: Union[None, SSLContext, dict, str, list, tuple] = None,
        sock: Optional[socket] = None,
        workers: int = 1,
        protocol: Optional[Type[Protocol]] = None,
        backlog: int = 100,
        register_sys_signals: bool = True,
        access_log: Optional[bool] = None,
        unix: Optional[str] = None,
        loop: AbstractEventLoop = None,
        reload_dir: Optional[Union[List[str], str]] = None,
        noisy_exceptions: Optional[bool] = None,
        motd: bool = True,
        fast: bool = False,
        verbosity: int = 0,
        motd_display: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Run the HTTP Server and listen until keyboard interrupt or term
        signal. On termination, drain connections before closing.

        :param host: Address to host on
        :type host: str
        :param port: Port to host on
        :type port: int
        :param debug: Enables debug output (slows server)
        :type debug: bool
        :param auto_reload: Reload app whenever its source code is changed.
                            Enabled by default in debug mode.
        :type auto_relaod: bool
        :param ssl: SSLContext, or location of certificate and key
                    for SSL encryption of worker(s)
        :type ssl: str, dict, SSLContext or list
        :param sock: Socket for the server to accept connections from
        :type sock: socket
        :param workers: Number of processes received before it is respected
        :type workers: int
        :param protocol: Subclass of asyncio Protocol class
        :type protocol: type[Protocol]
        :param backlog: a number of unaccepted connections that the system
                        will allow before refusing new connections
        :type backlog: int
        :param register_sys_signals: Register SIG* events
        :type register_sys_signals: bool
        :param access_log: Enables writing access logs (slows server)
        :type access_log: bool
        :param unix: Unix socket to listen on instead of TCP port
        :type unix: str
        :param noisy_exceptions: Log exceptions that are normally considered
                                 to be quiet/silent
        :type noisy_exceptions: bool
        :return: Nothing
        """
        self.prepare(
            host=host,
            port=port,
            dev=dev,
            debug=debug,
            auto_reload=auto_reload,
            ssl=ssl,
            sock=sock,
            workers=workers,
            protocol=protocol,
            backlog=backlog,
            register_sys_signals=register_sys_signals,
            access_log=access_log,
            unix=unix,
            loop=loop,
            reload_dir=reload_dir,
            noisy_exceptions=noisy_exceptions,
            motd=motd,
            fast=fast,
            verbosity=verbosity,
            motd_display=motd_display,
        )

        self.__class__.serve(primary=self)  # type: ignore

    def prepare(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        *,
        dev: bool = False,
        debug: bool = False,
        auto_reload: Optional[bool] = None,
        ssl: Union[None, SSLContext, dict, str, list, tuple] = None,
        sock: Optional[socket] = None,
        workers: int = 1,
        protocol: Optional[Type[Protocol]] = None,
        backlog: int = 100,
        register_sys_signals: bool = True,
        access_log: Optional[bool] = None,
        unix: Optional[str] = None,
        loop: AbstractEventLoop = None,
        reload_dir: Optional[Union[List[str], str]] = None,
        noisy_exceptions: Optional[bool] = None,
        motd: bool = True,
        fast: bool = False,
        verbosity: int = 0,
        motd_display: Optional[Dict[str, str]] = None,
    ) -> None:
        if dev:
            debug = True
            auto_reload = True

        self.state.verbosity = verbosity
        if not self.state.auto_reload:
            self.state.auto_reload = bool(auto_reload)

        if fast and workers != 1:
            raise RuntimeError("You cannot use both fast=True and workers=X")

        if motd_display:
            self.config.MOTD_DISPLAY.update(motd_display)

        if reload_dir:
            if isinstance(reload_dir, str):
                reload_dir = [reload_dir]

            for directory in reload_dir:
                direc = Path(directory)
                if not direc.is_dir():
                    logger.warning(
                        f"Directory {directory} could not be located"
                    )
                self.state.reload_dirs.add(Path(directory))

        if loop is not None:
            raise TypeError(
                "loop is not a valid argument. To use an existing loop, "
                "change to create_server().\nSee more: "
                "https://sanic.readthedocs.io/en/latest/sanic/deploying.html"
                "#asynchronous-support"
            )

        if (
            self.__class__.should_auto_reload()
            and os.environ.get("SANIC_SERVER_RUNNING") != "true"
        ):  # no cov
            return

        if sock is None:
            host, port = host or "127.0.0.1", port or 8000

        if protocol is None:
            protocol = (
                WebSocketProtocol if self.websocket_enabled else HttpProtocol
            )

        # Set explicitly passed configuration values
        for attribute, value in {
            "ACCESS_LOG": access_log,
            "AUTO_RELOAD": auto_reload,
            "MOTD": motd,
            "NOISY_EXCEPTIONS": noisy_exceptions,
        }.items():
            if value is not None:
                setattr(self.config, attribute, value)

        if fast:
            self.state.fast = True
            try:
                workers = len(os.sched_getaffinity(0))
            except AttributeError:  # no cov
                workers = os.cpu_count() or 1

        server_settings = self._helper(
            host=host,
            port=port,
            debug=debug,
            ssl=ssl,
            sock=sock,
            unix=unix,
            workers=workers,
            protocol=protocol,
            backlog=backlog,
            register_sys_signals=register_sys_signals,
        )
        self.state.server_info.append(
            ApplicationServerInfo(settings=server_settings)
        )

        if self.config.USE_UVLOOP is True or (
            self.config.USE_UVLOOP is _default and not OS_IS_WINDOWS
        ):
            try_use_uvloop()

    async def create_server(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        *,
        debug: bool = False,
        ssl: Union[None, SSLContext, dict, str, list, tuple] = None,
        sock: Optional[socket] = None,
        protocol: Type[Protocol] = None,
        backlog: int = 100,
        access_log: Optional[bool] = None,
        unix: Optional[str] = None,
        return_asyncio_server: bool = False,
        asyncio_server_kwargs: Dict[str, Any] = None,
        noisy_exceptions: Optional[bool] = None,
    ) -> Optional[AsyncioServer]:
        """
        Asynchronous version of :func:`run`.

        This method will take care of the operations necessary to invoke
        the *before_start* events via :func:`trigger_events` method invocation
        before starting the *sanic* app in Async mode.

        .. note::
            This does not support multiprocessing and is not the preferred
            way to run a :class:`Sanic` application.

        :param host: Address to host on
        :type host: str
        :param port: Port to host on
        :type port: int
        :param debug: Enables debug output (slows server)
        :type debug: bool
        :param ssl: SSLContext, or location of certificate and key
                    for SSL encryption of worker(s)
        :type ssl: SSLContext or dict
        :param sock: Socket for the server to accept connections from
        :type sock: socket
        :param protocol: Subclass of asyncio Protocol class
        :type protocol: type[Protocol]
        :param backlog: a number of unaccepted connections that the system
                        will allow before refusing new connections
        :type backlog: int
        :param access_log: Enables writing access logs (slows server)
        :type access_log: bool
        :param return_asyncio_server: flag that defines whether there's a need
                                      to return asyncio.Server or
                                      start it serving right away
        :type return_asyncio_server: bool
        :param asyncio_server_kwargs: key-value arguments for
                                      asyncio/uvloop create_server method
        :type asyncio_server_kwargs: dict
        :param noisy_exceptions: Log exceptions that are normally considered
                                 to be quiet/silent
        :type noisy_exceptions: bool
        :return: AsyncioServer if return_asyncio_server is true, else Nothing
        """

        if sock is None:
            host, port = host or "127.0.0.1", port or 8000

        if protocol is None:
            protocol = (
                WebSocketProtocol if self.websocket_enabled else HttpProtocol
            )

        # Set explicitly passed configuration values
        for attribute, value in {
            "ACCESS_LOG": access_log,
            "NOISY_EXCEPTIONS": noisy_exceptions,
        }.items():
            if value is not None:
                setattr(self.config, attribute, value)

        server_settings = self._helper(
            host=host,
            port=port,
            debug=debug,
            ssl=ssl,
            sock=sock,
            unix=unix,
            loop=get_event_loop(),
            protocol=protocol,
            backlog=backlog,
            run_async=return_asyncio_server,
        )

        if self.config.USE_UVLOOP is not _default:
            error_logger.warning(
                "You are trying to change the uvloop configuration, but "
                "this is only effective when using the run(...) method. "
                "When using the create_server(...) method Sanic will use "
                "the already existing loop."
            )

        main_start = server_settings.pop("main_start", None)
        main_stop = server_settings.pop("main_stop", None)
        if main_start or main_stop:
            logger.warning(
                "Listener events for the main process are not available "
                "with create_server()"
            )

        return await serve(
            asyncio_server_kwargs=asyncio_server_kwargs, **server_settings
        )

    def stop(self):
        """
        This kills the Sanic
        """
        if self.state.stage is not ServerStage.STOPPED:
            self.shutdown_tasks(timeout=0)
            for task in all_tasks():
                with suppress(AttributeError):
                    if task.get_name() == "RunServer":
                        task.cancel()
            get_event_loop().stop()

    def _helper(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        debug: bool = False,
        ssl: Union[None, SSLContext, dict, str, list, tuple] = None,
        sock: Optional[socket] = None,
        unix: Optional[str] = None,
        workers: int = 1,
        loop: AbstractEventLoop = None,
        protocol: Type[Protocol] = HttpProtocol,
        backlog: int = 100,
        register_sys_signals: bool = True,
        run_async: bool = False,
    ) -> Dict[str, Any]:
        """Helper function used by `run` and `create_server`."""
        if self.config.PROXIES_COUNT and self.config.PROXIES_COUNT < 0:
            raise ValueError(
                "PROXIES_COUNT cannot be negative. "
                "https://sanic.readthedocs.io/en/latest/sanic/config.html"
                "#proxy-configuration"
            )

        ssl = process_to_context(ssl)

        if not self.state.is_debug:
            self.state.mode = Mode.DEBUG if debug else Mode.PRODUCTION

        self.state.host = host or ""
        self.state.port = port or 0
        self.state.workers = workers
        self.state.ssl = ssl
        self.state.unix = unix
        self.state.sock = sock

        server_settings = {
            "protocol": protocol,
            "host": host,
            "port": port,
            "sock": sock,
            "unix": unix,
            "ssl": ssl,
            "app": self,
            "signal": ServerSignal(),
            "loop": loop,
            "register_sys_signals": register_sys_signals,
            "backlog": backlog,
        }

        self.motd(self.serve_location)

        if sys.stdout.isatty() and not self.state.is_debug:
            error_logger.warning(
                f"{Colors.YELLOW}Sanic is running in PRODUCTION mode. "
                "Consider using '--debug' or '--dev' while actively "
                f"developing your application.{Colors.END}"
            )

        # Register start/stop events
        for event_name, settings_name, reverse in (
            ("main_process_start", "main_start", False),
            ("main_process_stop", "main_stop", True),
        ):
            listeners = self.listeners[event_name].copy()
            if reverse:
                listeners.reverse()
            # Prepend sanic to the arguments when listeners are triggered
            listeners = [partial(listener, self) for listener in listeners]
            server_settings[settings_name] = listeners  # type: ignore

        if run_async:
            server_settings["run_async"] = True

        return server_settings

    def motd(self, serve_location):
        if self.config.MOTD:
            mode = [f"{self.state.mode},"]
            if self.state.fast:
                mode.append("goin' fast")
            if self.state.asgi:
                mode.append("ASGI")
            else:
                if self.state.workers == 1:
                    mode.append("single worker")
                else:
                    mode.append(f"w/ {self.state.workers} workers")

            display = {
                "mode": " ".join(mode),
                "server": self.state.server,
                "python": platform.python_version(),
                "platform": platform.platform(),
            }
            extra = {}
            if self.config.AUTO_RELOAD:
                reload_display = "enabled"
                if self.state.reload_dirs:
                    reload_display += ", ".join(
                        [
                            "",
                            *(
                                str(path.absolute())
                                for path in self.state.reload_dirs
                            ),
                        ]
                    )
                display["auto-reload"] = reload_display

            packages = []
            for package_name in SANIC_PACKAGES:
                module_name = package_name.replace("-", "_")
                try:
                    module = import_module(module_name)
                    packages.append(f"{package_name}=={module.__version__}")
                except ImportError:
                    ...

            if packages:
                display["packages"] = ", ".join(packages)

            if self.config.MOTD_DISPLAY:
                extra.update(self.config.MOTD_DISPLAY)

            logo = (
                get_logo(coffee=self.state.coffee)
                if self.config.LOGO == "" or self.config.LOGO is True
                else self.config.LOGO
            )

            MOTD.output(logo, serve_location, display, extra)

    @property
    def serve_location(self) -> str:
        serve_location = ""
        proto = "http"
        if self.state.ssl is not None:
            proto = "https"
        if self.state.unix:
            serve_location = f"{self.state.unix} {proto}://..."
        elif self.state.sock:
            serve_location = f"{self.state.sock.getsockname()} {proto}://..."
        elif self.state.host and self.state.port:
            # colon(:) is legal for a host only in an ipv6 address
            display_host = (
                f"[{self.state.host}]"
                if ":" in self.state.host
                else self.state.host
            )
            serve_location = f"{proto}://{display_host}:{self.state.port}"

        return serve_location

    @classmethod
    def should_auto_reload(cls) -> bool:
        return any(app.state.auto_reload for app in cls._app_registry.values())

    @classmethod
    def serve(cls, primary: Optional[Sanic] = None) -> None:
        apps = list(cls._app_registry.values())

        if not primary:
            try:
                primary = apps[0]
            except IndexError:
                raise RuntimeError("Did not find any applications.")

        reloader_start = primary.listeners.get("reload_process_start")
        reloader_stop = primary.listeners.get("reload_process_stop")
        # We want to run auto_reload if ANY of the applications have it enabled
        if (
            cls.should_auto_reload()
            and os.environ.get("SANIC_SERVER_RUNNING") != "true"
        ):  # no cov
            loop = new_event_loop()
            trigger_events(reloader_start, loop, primary)
            reload_dirs: Set[Path] = primary.state.reload_dirs.union(
                *(app.state.reload_dirs for app in apps)
            )
            reloader_helpers.watchdog(1.0, reload_dirs)
            trigger_events(reloader_stop, loop, primary)
            return

        # This exists primarily for unit testing
        if not primary.state.server_info:  # no cov
            for app in apps:
                app.state.server_info.clear()
            return

        primary_server_info = primary.state.server_info[0]
        primary.before_server_start(partial(primary._start_servers, apps=apps))

        try:
            primary_server_info.stage = ServerStage.SERVING

            if primary.state.workers > 1 and os.name != "posix":  # no cov
                logger.warn(
                    f"Multiprocessing is currently not supported on {os.name},"
                    " using workers=1 instead"
                )
                primary.state.workers = 1
            if primary.state.workers == 1:
                serve_single(primary_server_info.settings)
            elif primary.state.workers == 0:
                raise RuntimeError("Cannot serve with no workers")
            else:
                serve_multiple(
                    primary_server_info.settings, primary.state.workers
                )
        except BaseException:
            error_logger.exception(
                "Experienced exception while trying to serve"
            )
            raise
        finally:
            primary_server_info.stage = ServerStage.STOPPED
        logger.info("Server Stopped")
        for app in apps:
            app.state.server_info.clear()
            app.router.reset()
            app.signal_router.reset()

    async def _start_servers(
        self,
        primary: Sanic,
        _,
        apps: List[Sanic],
    ) -> None:
        for app in apps:
            if (
                app.name is not primary.name
                and app.state.workers != primary.state.workers
                and app.state.server_info
            ):
                message = (
                    f"The primary application {repr(primary)} is running "
                    f"with {primary.state.workers} worker(s). All "
                    "application instances will run with the same number. "
                    f"You requested {repr(app)} to run with "
                    f"{app.state.workers} worker(s), which will be ignored "
                    "in favor of the primary application."
                )
                if sys.stdout.isatty():
                    message = "".join(
                        [
                            Colors.YELLOW,
                            message,
                            Colors.END,
                        ]
                    )
                error_logger.warning(message, exc_info=True)
            for server_info in app.state.server_info:
                if server_info.stage is not ServerStage.SERVING:
                    app.state.primary = False
                    handlers = [
                        *server_info.settings.pop("main_start", []),
                        *server_info.settings.pop("main_stop", []),
                    ]
                    if handlers:
                        error_logger.warning(
                            f"Sanic found {len(handlers)} listener(s) on "
                            "secondary applications attached to the main "
                            "process. These will be ignored since main "
                            "process listeners can only be attached to your "
                            "primary application: "
                            f"{repr(primary)}"
                        )

                    if not server_info.settings["loop"]:
                        server_info.settings["loop"] = get_running_loop()

                    try:
                        server_info.server = await serve(
                            **server_info.settings,
                            run_async=True,
                            reuse_port=bool(primary.state.workers - 1),
                        )
                    except OSError as e:  # no cov
                        first_message = (
                            "An OSError was detected on startup. "
                            "The encountered error was: "
                        )
                        second_message = str(e)
                        if sys.stdout.isatty():
                            message_parts = [
                                Colors.YELLOW,
                                first_message,
                                Colors.RED,
                                second_message,
                                Colors.END,
                            ]
                        else:
                            message_parts = [first_message, second_message]
                        message = "".join(message_parts)
                        error_logger.warning(message, exc_info=True)
                        continue
                    primary.add_task(
                        self._run_server(app, server_info), name="RunServer"
                    )

    async def _run_server(
        self,
        app: RunnerMixin,
        server_info: ApplicationServerInfo,
    ) -> None:

        try:
            # We should never get to this point without a server
            # This is primarily to keep mypy happy
            if not server_info.server:  # no cov
                raise RuntimeError("Could not locate AsyncioServer")
            if app.state.stage is ServerStage.STOPPED:
                server_info.stage = ServerStage.SERVING
                await server_info.server.startup()
                await server_info.server.before_start()
                await server_info.server.after_start()
            await server_info.server.serve_forever()
        except CancelledError:
            # We should never get to this point without a server
            # This is primarily to keep mypy happy
            if not server_info.server:  # no cov
                raise RuntimeError("Could not locate AsyncioServer")
            await server_info.server.before_stop()
            await server_info.server.close()
            await server_info.server.after_stop()
        finally:
            server_info.stage = ServerStage.STOPPED
            server_info.server = None
