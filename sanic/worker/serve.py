import asyncio
import os
import socket
import warnings

from functools import partial
from multiprocessing.connection import Connection
from ssl import SSLContext
from typing import Any, Dict, List, Optional, Type, Union

from sanic.application.constants import ServerStage
from sanic.application.state import ApplicationServerInfo
from sanic.http.constants import HTTP
from sanic.log import error_logger
from sanic.models.server_types import Signal
from sanic.server.protocols.http_protocol import HttpProtocol
from sanic.server.runners import _serve_http_1, _serve_http_3
from sanic.worker.loader import AppLoader, CertLoader
from sanic.worker.multiplexer import WorkerMultiplexer
from sanic.worker.process import Worker, WorkerProcess


def worker_serve(
    host,
    port,
    app_name: str,
    monitor_publisher: Optional[Connection],
    app_loader: AppLoader,
    worker_state: Optional[Dict[str, Any]] = None,
    server_info: Optional[Dict[str, List[ApplicationServerInfo]]] = None,
    ssl: Optional[
        Union[SSLContext, Dict[str, Union[str, os.PathLike]]]
    ] = None,
    sock: Optional[socket.socket] = None,
    unix: Optional[str] = None,
    reuse_port: bool = False,
    loop=None,
    protocol: Type[asyncio.Protocol] = HttpProtocol,
    backlog: int = 100,
    register_sys_signals: bool = True,
    run_multiple: bool = False,
    run_async: bool = False,
    connections=None,
    signal=Signal(),
    state=None,
    asyncio_server_kwargs=None,
    version=HTTP.VERSION_1,
    config=None,
    passthru: Optional[Dict[str, Any]] = None,
):
    try:
        from sanic import Sanic

        if app_loader:
            app = app_loader.load()
        else:
            app = Sanic.get_app(app_name)

        app.refresh(passthru)
        app.setup_loop()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Hydrate server info if needed
        if server_info:
            for app_name, server_info_objects in server_info.items():
                a = Sanic.get_app(app_name)
                if not a.state.server_info:
                    a.state.server_info = []
                    for info in server_info_objects:
                        if not info.settings.get("app"):
                            info.settings["app"] = a
                        a.state.server_info.append(info)

        if isinstance(ssl, dict):
            cert_loader = CertLoader(ssl)
            ssl = cert_loader.load(app)
            for info in app.state.server_info:
                info.settings["ssl"] = ssl

        # When in a worker process, do some init
        worker_name = os.environ.get("SANIC_WORKER_NAME")
        if worker_name and worker_name.startswith(
            Worker.WORKER_PREFIX + WorkerProcess.SERVER_LABEL
        ):
            # Hydrate apps with any passed server info

            if monitor_publisher is None:
                raise RuntimeError(
                    "No restart publisher found in worker process"
                )
            if worker_state is None:
                raise RuntimeError("No worker state found in worker process")

            # Run secondary servers
            apps = list(Sanic._app_registry.values())
            app.before_server_start(partial(app._start_servers, apps=apps))
            for a in apps:
                a.multiplexer = WorkerMultiplexer(
                    monitor_publisher, worker_state
                )

        if app.debug:
            loop.set_debug(app.debug)

        app.asgi = False

        if app.state.server_info:
            primary_server_info = app.state.server_info[0]
            primary_server_info.stage = ServerStage.SERVING
        if config:
            app.update_config(config)

        if version is HTTP.VERSION_3:
            return _serve_http_3(host, port, app, loop, ssl)
        return _serve_http_1(
            host,
            port,
            app,
            ssl,
            sock,
            unix,
            reuse_port,
            loop,
            protocol,
            backlog,
            register_sys_signals,
            run_multiple,
            run_async,
            connections,
            signal,
            state,
            asyncio_server_kwargs,
        )
    except Exception as e:
        warnings.simplefilter("ignore", category=RuntimeWarning)
        if monitor_publisher:
            error_logger.exception(e)
            multiplexer = WorkerMultiplexer(monitor_publisher, {})
            multiplexer.terminate(True)
        else:
            raise e
