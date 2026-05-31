from __future__ import annotations

import os
import platform

from asyncio import (
    AbstractEventLoop,
    CancelledError,
    Protocol,
    all_tasks,
    get_event_loop,
    get_running_loop,
    new_event_loop,
)
from collections.abc import Mapping
from contextlib import suppress
from functools import partial
from importlib import import_module
from multiprocessing import (
    Manager,
    Pipe,
    get_context,
    get_start_method,
    set_start_method,
)
from multiprocessing.context import BaseContext
from pathlib import Path
from socket import SHUT_RDWR, socket
from ssl import SSLContext
from time import sleep
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Literal,
    Optional,
    Union,
    cast,
)

from sanic.application.ext import setup_ext
from sanic.application.logo import get_logo
from sanic.application.motd import MOTD
from sanic.application.state import ApplicationServerInfo, Mode, ServerStage
from sanic.base.meta import SanicMeta
from sanic.compat import OS_IS_WINDOWS, StartMethod
from sanic.exceptions import ServerKilled
from sanic.helpers import Default, _default, is_atty
from sanic.http.constants import HTTP
from sanic.http.tls import get_ssl_context, process_to_context
from sanic.http.tls.context import SanicSSLContext
from sanic.log import Colors, deprecation, error_logger, logger
from sanic.logging.setup import setup_logging
from sanic.models.handler_types import ListenerType
from sanic.server import Signal as ServerSignal
from sanic.server import try_use_uvloop
from sanic.server.async_server import AsyncioServer
from sanic.server.events import trigger_events
from sanic.server.goodbye import get_goodbye
from sanic.server.loop import try_windows_loop
from sanic.server.protocols.http_protocol import HttpProtocol
from sanic.server.protocols.websocket_protocol import WebSocketProtocol
from sanic.server.runners import serve
from sanic.server.socket import configure_socket, remove_unix_socket
from sanic.worker.loader import AppLoader
from sanic.worker.manager import WorkerManager
from sanic.worker.multiplexer import WorkerMultiplexer
from sanic.worker.reloader import Reloader
from sanic.worker.serve import worker_serve


if TYPE_CHECKING:
    from sanic import Sanic
    from sanic.application.state import ApplicationState
    from sanic.config import Config

SANIC_PACKAGES = ("sanic-routing", "sanic-testing", "sanic-ext")


HTTPVersion = Union[HTTP, Literal[1], Literal[3]]


class StartupMixin(metaclass=SanicMeta):
    _app_registry: ClassVar[dict[str, Sanic]]
    name: str
    asgi: bool
    config: Config
    listeners: dict[str, list[ListenerType[Any]]]
    state: ApplicationState
    websocket_enabled: bool
    multiplexer: WorkerMultiplexer

    test_mode: ClassVar[bool]
    start_method: ClassVar[StartMethod] = _default
    START_METHOD_SET: ClassVar[bool] = False

    def setup_loop(self) -> None:
        """Set up the event loop.

        An internal method that sets up the event loop to uvloop if
        possible, or a Windows selector loop if on Windows.

        Returns:
            None
        """
        if not self.asgi:
            if self.config.USE_UVLOOP is True or (
                isinstance(self.config.USE_UVLOOP, Default)
                and not OS_IS_WINDOWS
            ):
                try_use_uvloop()
            elif OS_IS_WINDOWS:
                try_windows_loop()

    @property
    def m(self) -> WorkerMultiplexer:
        """Interface for interacting with the worker processes

        This is a shortcut for `app.multiplexer`. It is available only in a
        worker process using the Sanic server. It allows you to interact with
        the worker processes, such as sending messages and commands.

        See [Access to the multiplexer](/en/guide/deployment/manager#access-to-the-multiplexer) for more information.

        Returns:
            WorkerMultiplexer: The worker multiplexer instance

        Examples:
            ```python
            app.m.restart()    # restarts the worker
            app.m.terminate()  # terminates the worker
            app.m.scale(4)     # scales the number of workers to 4
        ```
        """  # noqa: E501
        return self.multiplexer

    def make_coffee(self, *args, **kwargs):
        """
        Try for yourself! `sanic server:app --coffee`

         ```
         ▄████████▄
        ██       ██▀▀▄
        ███████████  █
        ███████████▄▄▀
         ▀███████▀

         ```
        """
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
        version: HTTPVersion = HTTP.VERSION_1,
        ssl: Union[None, SSLContext, dict, str, list, tuple] = None,
        sock: Optional[socket] = None,
        workers: int = 1,
        protocol: Optional[type[Protocol]] = None,
        backlog: int = 100,
        register_sys_signals: bool = True,
        access_log: Optional[bool] = None,
        unix: Optional[str] = None,
        loop: Optional[AbstractEventLoop] = None,
        reload_dir: Optional[Union[list[str], str]] = None,
        noisy_exceptions: Optional[bool] = None,
        motd: bool = True,
        fast: bool = False,
        verbosity: int = 0,
        motd_display: Optional[dict[str, str]] = None,
        auto_tls: bool = False,
        single_process: bool = False,
    ) -> None:
        """Run the HTTP Server and listen until keyboard interrupt or term signal. On termination, drain connections before closing.

        .. note::
            When you need control over running the Sanic instance, this is the method to use.
            However, in most cases the preferred method is to use the CLI command:

            ```sh
            sanic server:app`
            ```

        If you are using this method to run Sanic, make sure you do the following:

        1. Use `if __name__ == "__main__"` to guard the code.
        2. Do **NOT** define the app instance inside the `if` block.

        See [Dynamic Applications](/en/guide/deployment/app-loader) for more information about the second point.

        Args:
            host (Optional[str]): Address to host on.
            port (Optional[int]): Port to host on.
            dev (bool): Run the server in development mode.
            debug (bool): Enables debug output (slows server).
            auto_reload (Optional[bool]): Reload app whenever its source code is changed.
                Enabled by default in debug mode.
            version (HTTPVersion): HTTP Version.
            ssl (Union[None, SSLContext, dict, str, list, tuple]): SSLContext, or location of certificate and key
                for SSL encryption of worker(s).
            sock (Optional[socket]): Socket for the server to accept connections from.
            workers (int): Number of processes received before it is respected.
            protocol (Optional[Type[Protocol]]): Subclass of asyncio Protocol class.
            backlog (int): A number of unaccepted connections that the system will allow
                before refusing new connections.
            register_sys_signals (bool): Register SIG* events.
            access_log (Optional[bool]): Enables writing access logs (slows server).
            unix (Optional[str]): Unix socket to listen on instead of TCP port.
            loop (Optional[AbstractEventLoop]): AsyncIO event loop.
            reload_dir (Optional[Union[List[str], str]]): Directory to watch for code changes, if auto_reload is True.
            noisy_exceptions (Optional[bool]): Log exceptions that are normally considered to be quiet/silent.
            motd (bool): Display Message of the Day.
            fast (bool): Enable fast mode.
            verbosity (int): Verbosity level.
            motd_display (Optional[Dict[str, str]]): Customize Message of the Day display.
            auto_tls (bool): Enable automatic TLS certificate handling.
            single_process (bool): Enable single process mode.

        Returns:
            None

        Raises:
            RuntimeError: Raised when attempting to serve HTTP/3 as a secondary server.
            RuntimeError: Raised when attempting to use both `fast` and `workers`.
            RuntimeError: Raised when attempting to use `single_process` with `fast`, `workers`, or `auto_reload`.
            TypeError: Raised when attempting to use `loop` with `create_server`.
            ValueError: Raised when `PROXIES_COUNT` is negative.

        Examples:
            ```python
            from sanic import Sanic, Request, json

            app = Sanic("TestApp")


            @app.get("/")
            async def handler(request: Request):
                return json({"foo": "bar"})


            if __name__ == "__main__":
                app.run(port=9999, dev=True)
            ```
        """  # noqa: E501
        self.prepare(
            host=host,
            port=port,
            dev=dev,
            debug=debug,
            auto_reload=auto_reload,
            version=version,
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
            auto_tls=auto_tls,
            single_process=single_process,
        )

        if single_process:
            serve = self.__class__.serve_single
        else:
            serve = self.__class__.serve
        serve(primary=self)  # type: ignore

    def prepare(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        *,
        dev: bool = False,
        debug: bool = False,
        auto_reload: Optional[bool] = None,
        version: HTTPVersion = HTTP.VERSION_1,
        ssl: Union[None, SSLContext, dict, str, list, tuple] = None,
        sock: Optional[socket] = None,
        workers: int = 1,
        protocol: Optional[type[Protocol]] = None,
        backlog: int = 100,
        register_sys_signals: bool = True,
        access_log: Optional[bool] = None,
        unix: Optional[str] = None,
        loop: Optional[AbstractEventLoop] = None,
        reload_dir: Optional[Union[list[str], str]] = None,
        noisy_exceptions: Optional[bool] = None,
        motd: bool = True,
        fast: bool = False,
        verbosity: int = 0,
        motd_display: Optional[dict[str, str]] = None,
        coffee: bool = False,
        auto_tls: bool = False,
        single_process: bool = False,
    ) -> None:
        """Prepares one or more Sanic applications to be served simultaneously.

        This low-level API is typically used when you need to run multiple Sanic applications at the same time. Once prepared, `Sanic.serve()` should be called in the `if __name__ == "__main__"` block.

        .. note::
            "Preparing" and "serving" with this function is equivalent to using `app.run` for a single instance. This should only be used when running multiple applications at the same time.

        Args:
            host (Optional[str], optional): Hostname to listen on. Defaults to `None`.
            port (Optional[int], optional): Port to listen on. Defaults to `None`.
            dev (bool, optional): Development mode. Defaults to `False`.
            debug (bool, optional): Debug mode. Defaults to `False`.
            auto_reload (Optional[bool], optional): Auto reload feature. Defaults to `None`.
            version (HTTPVersion, optional): HTTP version to use. Defaults to `HTTP.VERSION_1`.
            ssl (Union[None, SSLContext, dict, str, list, tuple], optional): SSL configuration. Defaults to `None`.
            sock (Optional[socket], optional): Socket to bind to. Defaults to `None`.
            workers (int, optional): Number of worker processes. Defaults to `1`.
            protocol (Optional[Type[Protocol]], optional): Custom protocol class. Defaults to `None`.
            backlog (int, optional): Maximum number of pending connections. Defaults to `100`.
            register_sys_signals (bool, optional): Register system signals. Defaults to `True`.
            access_log (Optional[bool], optional): Access log. Defaults to `None`.
            unix (Optional[str], optional): Unix socket. Defaults to `None`.
            loop (Optional[AbstractEventLoop], optional): Event loop. Defaults to `None`.
            reload_dir (Optional[Union[List[str], str]], optional): Reload directory. Defaults to `None`.
            noisy_exceptions (Optional[bool], optional): Display exceptions. Defaults to `None`.
            motd (bool, optional): Display message of the day. Defaults to `True`.
            fast (bool, optional): Fast mode. Defaults to `False`.
            verbosity (int, optional): Verbosity level. Defaults to `0`.
            motd_display (Optional[Dict[str, str]], optional): Custom MOTD display. Defaults to `None`.
            coffee (bool, optional): Coffee mode. Defaults to `False`.
            auto_tls (bool, optional): Auto TLS. Defaults to `False`.
            single_process (bool, optional): Single process mode. Defaults to `False`.

        Raises:
            RuntimeError: Raised when attempting to serve HTTP/3 as a secondary server.
            RuntimeError: Raised when attempting to use both `fast` and `workers`.
            RuntimeError: Raised when attempting to use `single_process` with `fast`, `workers`, or `auto_reload`.
            TypeError: Raised when attempting to use `loop` with `create_server`.
            ValueError: Raised when `PROXIES_COUNT` is negative.

        Examples:
            ```python
            if __name__ == "__main__":
                app.prepare()
                app.serve()
            ```
        """  # noqa: E501
        if version == 3 and self.state.server_info:
            raise RuntimeError(
                "Serving HTTP/3 instances as a secondary server is "
                "not supported. There can only be a single HTTP/3 worker "
                "and it must be the first instance prepared."
            )

        if dev:
            debug = True
            auto_reload = True

        if debug and access_log is None:
            access_log = True

        self.state.verbosity = verbosity
        if not self.state.auto_reload:
            self.state.auto_reload = bool(auto_reload)

        if fast and workers != 1:
            raise RuntimeError("You cannot use both fast=True and workers=X")

        if single_process and (fast or (workers > 1) or auto_reload):
            raise RuntimeError(
                "Single process cannot be run with multiple workers "
                "or auto-reload"
            )

        if register_sys_signals is False and not single_process:
            raise RuntimeError(
                "Cannot run Sanic.serve with register_sys_signals=False. "
                "Use Sanic.serve_single."
            )

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

        if sock is None:
            host, port = self.get_address(host, port, version, auto_tls)

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

        if coffee:
            self.state.coffee = True

        server_settings = self._helper(
            host=host,
            port=port,
            debug=debug,
            version=version,
            ssl=ssl,
            sock=sock,
            unix=unix,
            workers=workers,
            protocol=protocol,
            backlog=backlog,
            register_sys_signals=register_sys_signals,
            auto_tls=auto_tls,
        )
        self.state.server_info.append(
            ApplicationServerInfo(settings=server_settings)
        )

        # if self.config.USE_UVLOOP is True or (
        #     self.config.USE_UVLOOP is _default and not OS_IS_WINDOWS
        # ):
        #     try_use_uvloop()

    async def create_server(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        *,
        debug: bool = False,
        ssl: Union[None, SSLContext, dict, str, list, tuple] = None,
        sock: Optional[socket] = None,
        protocol: Optional[type[Protocol]] = None,
        backlog: int = 100,
        access_log: Optional[bool] = None,
        unix: Optional[str] = None,
        return_asyncio_server: bool = True,
        asyncio_server_kwargs: Optional[dict[str, Any]] = None,
        noisy_exceptions: Optional[bool] = None,
    ) -> Optional[AsyncioServer]:
        """
        Low level API for creating a Sanic Server instance.

        This method will create a Sanic Server instance, but will not start
        it. This is useful for integrating Sanic into other systems. But, you
        should take caution when using it as it is a low level API and does
        not perform any of the lifecycle events.

        .. note::
            This does not support multiprocessing and is not the preferred
            way to run a Sanic application. Proceed with caution.

        You will need to start the server yourself as shown in the example
        below. You are responsible for the lifecycle of the server, including
        app startup using `await app.startup()`. No events will be triggered
        for you, so you will need to trigger them yourself if wanted.

        Args:
            host (Optional[str]): Address to host on.
            port (Optional[int]): Port to host on.
            debug (bool): Enables debug output (slows server).
            ssl (Union[None, SSLContext, dict, str, list, tuple]): SSLContext,
                or location of certificate and key for SSL encryption
                of worker(s).
            sock (Optional[socket]): Socket for the server to accept
                connections from.
            protocol (Optional[Type[Protocol]]): Subclass of
                `asyncio.Protocol` class.
            backlog (int): Number of unaccepted connections that the system
                will allow before refusing new connections.
            access_log (Optional[bool]): Enables writing access logs
                (slows server).
            return_asyncio_server (bool): _DEPRECATED_
            asyncio_server_kwargs (Optional[Dict[str, Any]]): Key-value
                arguments for asyncio/uvloop `create_server` method.
            noisy_exceptions (Optional[bool]): Log exceptions that are normally
                considered to be quiet/silent.

        Returns:
            Optional[AsyncioServer]: AsyncioServer if `return_asyncio_server`
                is `True` else `None`.

        Examples:
            ```python
            import asyncio
            import uvloop
            from sanic import Sanic, response


            app = Sanic("Example")


            @app.route("/")
            async def test(request):
                return response.json({"answer": "42"})


            async def main():
                server = await app.create_server()
                await server.startup()
                await server.serve_forever()


            if __name__ == "__main__":
                asyncio.set_event_loop(uvloop.new_event_loop())
                asyncio.run(main())
            ```
        """

        if sock is None:
            host, port = host, port = self.get_address(host, port)

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

        if not return_asyncio_server:
            return_asyncio_server = True
            deprecation(
                "The `return_asyncio_server` argument is deprecated and "
                "ignored. It will be removed in v24.3.",
                24.3,
            )

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

        if not isinstance(self.config.USE_UVLOOP, Default):
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

    def stop(self, terminate: bool = True, unregister: bool = False) -> None:
        """This kills the Sanic server, cleaning up after itself.

        Args:
            terminate (bool): Force kill all requests immediately without
                allowing them to finish processing.
            unregister (bool): Unregister the app from the global registry.

        Returns:
            None
        """
        if terminate and hasattr(self, "multiplexer"):
            self.multiplexer.terminate()
        if self.state.stage is not ServerStage.STOPPED:
            self.shutdown_tasks(timeout=0)  # type: ignore
            for task in all_tasks():
                with suppress(AttributeError):
                    if task.get_name() == "RunServer":
                        task.cancel()
            get_event_loop().stop()

        if unregister:
            self.__class__.unregister_app(self)  # type: ignore

    def _helper(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        debug: bool = False,
        version: HTTPVersion = HTTP.VERSION_1,
        ssl: Union[None, SSLContext, dict, str, list, tuple] = None,
        sock: Optional[socket] = None,
        unix: Optional[str] = None,
        workers: int = 1,
        loop: Optional[AbstractEventLoop] = None,
        protocol: type[Protocol] = HttpProtocol,
        backlog: int = 100,
        register_sys_signals: bool = True,
        run_async: bool = False,
        auto_tls: bool = False,
    ) -> dict[str, Any]:
        """Helper function used by `run` and `create_server`."""
        if self.config.PROXIES_COUNT and self.config.PROXIES_COUNT < 0:
            raise ValueError(
                "PROXIES_COUNT cannot be negative. "
                "https://sanic.readthedocs.io/en/latest/sanic/config.html"
                "#proxy-configuration"
            )

        if not self.state.is_debug:
            self.state.mode = Mode.DEBUG if debug else Mode.PRODUCTION

        setup_logging(self.state.is_debug, self.config.NO_COLOR)

        if isinstance(version, int):
            version = HTTP(version)

        ssl = process_to_context(ssl)
        if version is HTTP.VERSION_3 or auto_tls:
            if TYPE_CHECKING:
                self = cast(Sanic, self)
            ssl = get_ssl_context(self, ssl)

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
            "version": version,
            "sock": sock,
            "unix": unix,
            "ssl": ssl,
            "app": self,
            "signal": ServerSignal(),
            "loop": loop,
            "register_sys_signals": register_sys_signals,
            "backlog": backlog,
        }

        self.motd(server_settings=server_settings)

        if (
            is_atty()
            and not self.state.is_debug
            and not os.environ.get("SANIC_IGNORE_PRODUCTION_WARNING")
        ):
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

    def motd(
        self,
        server_settings: Optional[dict[str, Any]] = None,
    ) -> None:
        """Outputs the message of the day (MOTD).

        It generally can only be called once per process, and is usually
        called by the `run` method in the main process.

        Args:
            server_settings (Optional[Dict[str, Any]], optional): Settings for
                the server. Defaults to `None`.

        Returns:
            None
        """
        if (
            os.environ.get("SANIC_WORKER_NAME")
            or os.environ.get("SANIC_MOTD_OUTPUT")
            or os.environ.get("SANIC_WORKER_PROCESS")
            or os.environ.get("SANIC_SERVER_RUNNING")
        ):
            return
        serve_location = self.get_server_location(server_settings)
        if self.config.MOTD:
            logo = get_logo(coffee=self.state.coffee)
            display, extra = self.get_motd_data(server_settings)

            MOTD.output(logo, serve_location, display, extra)

    def get_motd_data(
        self, server_settings: Optional[dict[str, Any]] = None
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Retrieves the message of the day (MOTD) data.

        Args:
            server_settings (Optional[Dict[str, Any]], optional): Settings for
                the server. Defaults to `None`.

        Returns:
            Tuple[Dict[str, Any], Dict[str, Any]]: A tuple containing two
                dictionaries with the relevant MOTD data.
        """

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

        if server_settings:
            server = ", ".join(
                (
                    self.state.server,
                    server_settings["version"].display(),  # type: ignore
                )
            )
        else:
            server = "ASGI" if self.asgi else "unknown"  # type: ignore

        display = {
            "app": self.name,
            "mode": " ".join(mode),
            "server": server,
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
                packages.append(f"{package_name}=={module.__version__}")  # type: ignore
            except ImportError:  # no cov
                ...

        if packages:
            display["packages"] = ", ".join(packages)

        if self.config.MOTD_DISPLAY:
            extra.update(self.config.MOTD_DISPLAY)

        return display, extra

    @property
    def serve_location(self) -> str:
        """Retrieve the server location.

        Returns:
            str: The server location.
        """
        try:
            server_settings = self.state.server_info[0].settings
            return self.get_server_location(server_settings)
        except IndexError:
            location = "ASGI" if self.asgi else "unknown"  # type: ignore
            return f"http://<{location}>"

    @staticmethod
    def get_server_location(
        server_settings: Optional[dict[str, Any]] = None,
    ) -> str:
        """Using the server settings, retrieve the server location.

        Args:
            server_settings (Optional[Dict[str, Any]], optional): Settings for
                the server. Defaults to `None`.

        Returns:
            str: The server location.
        """
        serve_location = ""
        proto = "http"
        if not server_settings:
            return serve_location

        host = server_settings["host"]
        port = server_settings["port"]

        if server_settings.get("ssl") is not None:
            proto = "https"
        if server_settings.get("unix"):
            serve_location = f"{server_settings['unix']} {proto}://..."
        elif server_settings.get("sock"):
            host, port, *_ = server_settings["sock"].getsockname()

        if not serve_location and host and port:
            # colon(:) is legal for a host only in an ipv6 address
            display_host = f"[{host}]" if ":" in host else host
            serve_location = f"{proto}://{display_host}:{port}"

        return serve_location

    @staticmethod
    def get_address(
        host: Optional[str],
        port: Optional[int],
        version: HTTPVersion = HTTP.VERSION_1,
        auto_tls: bool = False,
    ) -> tuple[str, int]:
        """Retrieve the host address and port, with default values based on the given parameters.

        Args:
            host (Optional[str]): Host IP or FQDN for the service to use. Defaults to `"127.0.0.1"`.
            port (Optional[int]): Port number. Defaults to `8443` if version is 3 or `auto_tls=True`, else `8000`
            version (HTTPVersion, optional): HTTP Version. Defaults to `HTTP.VERSION_1` (HTTP/1.1).
            auto_tls (bool, optional): Automatic TLS flag. Defaults to `False`.

        Returns:
            Tuple[str, int]: Tuple containing the host and port
        """  # noqa: E501
        host = host or "127.0.0.1"
        port = port or (8443 if (version == 3 or auto_tls) else 8000)
        return host, port

    @classmethod
    def should_auto_reload(cls) -> bool:
        """Check if any applications have auto-reload enabled.

        Returns:
            bool: `True` if any applications have auto-reload enabled, else
                `False`.
        """
        return any(app.state.auto_reload for app in cls._app_registry.values())

    @classmethod
    def _get_startup_method(cls) -> str:
        return (
            cls.start_method
            if not isinstance(cls.start_method, Default)
            else "spawn"
        )

    @classmethod
    def _set_startup_method(cls) -> None:
        if cls.START_METHOD_SET and not cls.test_mode:
            return

        method = cls._get_startup_method()
        try:
            set_start_method(method, force=cls.test_mode)
        except RuntimeError:
            ctx = get_context()
            actual = ctx.get_start_method()
            if actual != method:
                raise RuntimeError(
                    f"Start method '{method}' was requested, but '{actual}' "
                    "was already set.\nFor more information, see: "
                    "https://sanic.dev/en/guide/running/manager.html#overcoming-a-coderuntimeerrorcode"
                ) from None
            else:
                raise
        cls.START_METHOD_SET = True

    @classmethod
    def _get_context(cls) -> BaseContext:
        method = cls._get_startup_method()
        logger.debug("Creating multiprocessing context using '%s'", method)
        actual = get_start_method()
        if method != actual:
            raise RuntimeError(
                f"Start method '{method}' was requested, but '{actual}' "
                "was already set.\nFor more information, see: "
                "https://sanic.dev/en/guide/running/manager.html#overcoming-a-coderuntimeerrorcode"
            ) from None
        return get_context()

    @classmethod
    def serve(
        cls,
        primary: Optional[Sanic] = None,
        *,
        app_loader: Optional[AppLoader] = None,
        factory: Optional[Callable[[], Sanic]] = None,
    ) -> None:
        """Serve one or more Sanic applications.

        This is the main entry point for running Sanic applications. It
        should be called in the `if __name__ == "__main__"` block.

        Args:
            primary (Optional[Sanic], optional): The primary Sanic application
                to serve. Defaults to `None`.
            app_loader (Optional[AppLoader], optional): An AppLoader instance
                to use for loading applications. Defaults to `None`.
            factory (Optional[Callable[[], Sanic]], optional): A factory
                function to use for loading applications. Defaults to `None`.

        Raises:
            RuntimeError: Raised when no applications are found.
            RuntimeError: Raised when no server information is found for the
                primary application.
            RuntimeError: Raised when attempting to use `loop` with
                `create_server`.
            RuntimeError: Raised when attempting to use `single_process` with
                `fast`, `workers`, or `auto_reload`.
            RuntimeError: Raised when attempting to serve HTTP/3 as a
                secondary server.
            RuntimeError: Raised when attempting to use both `fast` and
                `workers`.
            TypeError: Raised when attempting to use `loop` with
                `create_server`.
            ValueError: Raised when `PROXIES_COUNT` is negative.

        Examples:
            ```python
            if __name__ == "__main__":
                app.prepare()
                Sanic.serve()
            ```
        """
        cls._set_startup_method()
        os.environ["SANIC_MOTD_OUTPUT"] = "true"
        apps = list(cls._app_registry.values())
        if factory:
            primary = factory()
        else:
            if not primary:
                if app_loader:
                    primary = app_loader.load()
                if not primary:
                    try:
                        primary = apps[0]
                    except IndexError:
                        raise RuntimeError(
                            "Did not find any applications."
                        ) from None

            # This exists primarily for unit testing
            if not primary.state.server_info:  # no cov
                for app in apps:
                    app.state.server_info.clear()
                return

        try:
            primary_server_info = primary.state.server_info[0]
        except IndexError:
            raise RuntimeError(
                f"No server information found for {primary.name}. Perhaps you "
                "need to run app.prepare(...)?"
            ) from None

        socks = []
        sync_manager = Manager()
        worker_state: Mapping[str, Any] = {"state": "NONE"}
        setup_ext(primary)
        exit_code = 0
        try:
            primary_server_info.settings.pop("main_start", None)
            primary_server_info.settings.pop("main_stop", None)
            main_start = primary.listeners.get("main_process_start")
            main_stop = primary.listeners.get("main_process_stop")
            app = primary_server_info.settings.pop("app")
            app.setup_loop()
            loop = new_event_loop()
            trigger_events(main_start, loop, primary)

            socks = [
                sock
                for sock in [
                    configure_socket(server_info.settings)
                    for app in apps
                    for server_info in app.state.server_info
                ]
                if sock
            ]
            primary_server_info.settings["run_multiple"] = True
            monitor_sub, monitor_pub = Pipe(True)
            worker_state = sync_manager.dict()
            kwargs: dict[str, Any] = {
                **primary_server_info.settings,
                "monitor_publisher": monitor_pub,
                "worker_state": worker_state,
            }

            if not app_loader:
                if factory:
                    app_loader = AppLoader(factory=factory)
                else:
                    app_loader = AppLoader(
                        factory=partial(cls.get_app, app.name)  # type: ignore
                    )
            kwargs["app_name"] = app.name
            kwargs["app_loader"] = app_loader
            kwargs["server_info"] = {}
            kwargs["passthru"] = {
                "auto_reload": app.auto_reload,
                "state": {
                    "verbosity": app.state.verbosity,
                    "mode": app.state.mode,
                },
                "config": {
                    "ACCESS_LOG": app.config.ACCESS_LOG,
                    "NOISY_EXCEPTIONS": app.config.NOISY_EXCEPTIONS,
                },
                "shared_ctx": app.shared_ctx.__dict__,
            }
            for app in apps:
                kwargs["server_info"][app.name] = []
                for server_info in app.state.server_info:
                    server_info.settings = {
                        k: v
                        for k, v in server_info.settings.items()
                        if k not in ("main_start", "main_stop", "app", "ssl")
                    }
                    kwargs["server_info"][app.name].append(server_info)

            ssl = kwargs.get("ssl")

            if isinstance(ssl, SanicSSLContext):
                kwargs["ssl"] = ssl.sanic

            manager = WorkerManager(
                primary.state.workers,
                worker_serve,
                kwargs,
                cls._get_context(),
                (monitor_pub, monitor_sub),
                worker_state,
            )
            if cls.should_auto_reload():
                reload_dirs: set[Path] = primary.state.reload_dirs.union(
                    *(app.state.reload_dirs for app in apps)
                )
                reloader = Reloader(monitor_pub, 0, reload_dirs, app_loader)
                manager.manage("Reloader", reloader, {}, transient=False)

            inspector = None
            if primary.config.INSPECTOR:
                display, extra = primary.get_motd_data()
                packages = [
                    pkg.strip() for pkg in display["packages"].split(",")
                ]
                module = import_module("sanic")
                sanic_version = f"sanic=={module.__version__}"  # type: ignore
                app_info = {
                    **display,
                    "packages": [sanic_version, *packages],
                    "extra": extra,
                }
                inspector = primary.inspector_class(
                    monitor_pub,
                    app_info,
                    worker_state,
                    primary.config.INSPECTOR_HOST,
                    primary.config.INSPECTOR_PORT,
                    primary.config.INSPECTOR_API_KEY,
                    primary.config.INSPECTOR_TLS_KEY,
                    primary.config.INSPECTOR_TLS_CERT,
                )
                manager.manage("Inspector", inspector, {}, transient=False)

            primary._inspector = inspector
            primary._manager = manager

            ready = primary.listeners["main_process_ready"]
            trigger_events(ready, loop, primary)

            manager.run()
        except ServerKilled:
            exit_code = 1
        except BaseException:
            kwargs = primary_server_info.settings
            error_logger.exception(
                "Experienced exception while trying to serve"
            )
            raise
        finally:
            logger.info("Server Stopped")
            for app in apps:
                app.state.server_info.clear()
                app.router.reset()
                app.signal_router.reset()

            for sock in socks:
                try:
                    sock.shutdown(SHUT_RDWR)
                except OSError:
                    ...
                sock.close()
            socks = []

            trigger_events(main_stop, loop, primary)

            loop.close()
            cls._cleanup_env_vars()
            cls._cleanup_apps()

            limit = 100
            while cls._get_process_states(worker_state):
                sleep(0.1)
                limit -= 1
                if limit <= 0:
                    error_logger.warning(
                        "Worker shutdown timed out. "
                        "Some processes may still be running."
                    )
                    break
            sync_manager.shutdown()
            unix = kwargs.get("unix")
            if unix:
                remove_unix_socket(unix)
            logger.debug(get_goodbye())
        if exit_code:
            os._exit(exit_code)

    @staticmethod
    def _get_process_states(worker_state) -> list[str]:
        return [
            state
            for s in worker_state.values()
            if (
                (state := s.get("state"))
                and state not in ("TERMINATED", "FAILED", "COMPLETED", "NONE")
            )
        ]

    @classmethod
    def serve_single(cls, primary: Optional[Sanic] = None) -> None:
        """Serve a single process of a Sanic application.

        Similar to `serve`, but only serves a single process. When used,
        certain features are disabled, such as `fast`, `workers`,
        `multiplexer`, `auto_reload`, and the Inspector. It is almost
        never needed to use this method directly. Instead, you should
        use the CLI:

        ```sh
        sanic app.sanic:app --single-process
        ```

        Or, if you need to do it programmatically, you should use the
        `single_process` argument of `run`:

        ```python
        app.run(single_process=True)
        ```

        Args:
            primary (Optional[Sanic], optional): The primary Sanic application
                to serve. Defaults to `None`.

        Raises:
            RuntimeError: Raised when no applications are found.
            RuntimeError: Raised when no server information is found for the
                primary application.
            RuntimeError: Raised when attempting to serve HTTP/3 as a
                secondary server.
            RuntimeError: Raised when attempting to use both `fast` and
                `workers`.
            ValueError: Raised when `PROXIES_COUNT` is negative.
        """
        os.environ["SANIC_MOTD_OUTPUT"] = "true"
        apps = list(cls._app_registry.values())

        if not primary:
            try:
                primary = apps[0]
            except IndexError:
                raise RuntimeError("Did not find any applications.")

        # This exists primarily for unit testing
        if not primary.state.server_info:  # no cov
            for app in apps:
                app.state.server_info.clear()
            return

        primary_server_info = primary.state.server_info[0]
        primary.before_server_start(partial(primary._start_servers, apps=apps))
        kwargs = {
            k: v
            for k, v in primary_server_info.settings.items()
            if k
            not in (
                "main_start",
                "main_stop",
                "app",
            )
        }
        kwargs["app_name"] = primary.name
        kwargs["app_loader"] = None
        sock = configure_socket(kwargs)

        kwargs["server_info"] = {}
        kwargs["server_info"][primary.name] = []
        for server_info in primary.state.server_info:
            server_info.settings = {
                k: v
                for k, v in server_info.settings.items()
                if k not in ("main_start", "main_stop", "app")
            }
            kwargs["server_info"][primary.name].append(server_info)

        try:
            worker_serve(monitor_publisher=None, **kwargs)
        except BaseException:
            error_logger.exception(
                "Experienced exception while trying to serve"
            )
            raise
        finally:
            logger.info("Server Stopped")
            for app in apps:
                app.state.server_info.clear()
                app.router.reset()
                app.signal_router.reset()

            if sock:
                sock.close()

            cls._cleanup_env_vars()
            cls._cleanup_apps()

    async def _start_servers(
        self,
        primary: Sanic,
        _,
        apps: list[Sanic],
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
                if is_atty():
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
                    if handlers:  # no cov
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

                    serve_args: dict[str, Any] = {
                        **server_info.settings,
                        "run_async": True,
                        "reuse_port": bool(primary.state.workers - 1),
                    }
                    if "app" not in serve_args:
                        serve_args["app"] = app
                    try:
                        server_info.server = await serve(**serve_args)
                    except OSError as e:  # no cov
                        first_message = (
                            "An OSError was detected on startup. "
                            "The encountered error was: "
                        )
                        second_message = str(e)
                        if is_atty():
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
        app: StartupMixin,
        server_info: ApplicationServerInfo,
    ) -> None:  # no cov
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

    @staticmethod
    def _cleanup_env_vars():
        variables = (
            "SANIC_RELOADER_PROCESS",
            "SANIC_IGNORE_PRODUCTION_WARNING",
            "SANIC_WORKER_NAME",
            "SANIC_MOTD_OUTPUT",
            "SANIC_WORKER_PROCESS",
            "SANIC_SERVER_RUNNING",
        )
        for var in variables:
            try:
                del os.environ[var]
            except KeyError:
                ...

    @classmethod
    def _cleanup_apps(cls):
        for app in cls._app_registry.values():
            app.state.server_info.clear()
            app.router.reset()
            app.signal_router.reset()
