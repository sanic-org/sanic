from __future__ import annotations

import random

from asyncio import (
    Task,
    get_running_loop,
    sleep,
)
from asyncio import (
    run as run_async,
)
from dataclasses import asdict, dataclass
from datetime import datetime
from inspect import isawaitable
from multiprocessing.connection import Connection
from os import environ
from pathlib import Path
from signal import SIGINT, SIGTERM, signal
from string import ascii_lowercase, ascii_uppercase
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Dict,
    Mapping,
    Optional,
    Tuple,
    Union,
)

from websockets import WebSocketException, connection
from websockets.legacy.client import Connect, WebSocketClientProtocol


try:
    from websockets.connection import State
except ImportError:
    from websockets.protocol import State

from sanic.exceptions import Unauthorized
from sanic.helpers import Default, _default
from sanic.log import logger
from sanic.request import Request
from sanic.response import json
from sanic.server.websockets.impl import WebsocketImplProtocol


try:
    from ujson import dumps as dump_json
    from ujson import loads as load_json
except ImportError:
    from json import dumps as dump_json
    from json import loads as load_json

if TYPE_CHECKING:
    from sanic import Sanic


@dataclass
class NodeState:
    info: Dict[str, Any]
    workers: Dict[str, Any]


@dataclass
class HubState:
    nodes: Dict[str, NodeState]


class HubConnection(Connect):
    MAX_RETRIES = 6
    BACKOFF_MAX = 15

    async def __aiter__(self) -> AsyncIterator[WebSocketClientProtocol]:
        backoff_delay = self.BACKOFF_MIN
        failures = 0
        while True:
            if failures >= self.MAX_RETRIES:
                raise RuntimeError(
                    "Could not connect to bridge "
                    f"after {self.MAX_RETRIES} retries"
                )
            try:
                async with self as protocol:
                    if failures > 0:
                        self.logger.info(
                            "! connect succeeded after %d failures", failures
                        )
                    failures = 0
                    yield protocol
            except Exception:
                # Add a random initial delay between 0 and 5 seconds.
                # See 7.2.3. Recovering from Abnormal Closure in RFC 6455.
                if backoff_delay == self.BACKOFF_MIN:
                    initial_delay = random.random() * self.BACKOFF_INITIAL
                    self.logger.info(
                        "! connect failed; reconnecting in %.1f seconds",
                        initial_delay,
                    )
                    self.logger.debug("Exception", exc_info=True)
                    await sleep(initial_delay)
                else:
                    self.logger.info(
                        "! connect failed again; retrying in %d seconds",
                        int(backoff_delay),
                    )
                    self.logger.debug("Exception", exc_info=True)
                    await sleep(int(backoff_delay))
                # Increase delay with truncated exponential backoff.
                backoff_delay = backoff_delay * self.BACKOFF_FACTOR
                backoff_delay = min(backoff_delay, self.BACKOFF_MAX)
                failures += 1
                continue
            else:
                # Connection succeeded - reset backoff delay
                backoff_delay = self.BACKOFF_MIN


class NodeClient:
    def __init__(self, hub_host: str, hub_port: int) -> None:
        self.hub_host = hub_host
        self.hub_port = hub_port
        self._run = True
        self._heartbeat_task: Optional[Task] = None
        self._command_task: Optional[Task] = None

    async def run(self, state_getter) -> None:
        loop = get_running_loop()
        try:
            async for ws in HubConnection(
                f"ws://{self.hub_host}:{self.hub_port}/hub"
            ):
                try:
                    self._cancel_tasks()
                    self._heartbeat_task = loop.create_task(
                        self._heartbeat(ws, state_getter)
                    )
                    self._command_task = loop.create_task(self._command(ws))
                    while self._run and ws.state is State.OPEN:
                        await sleep(1)
                except WebSocketException:
                    logger.debug("Connection to hub dropped")
                finally:
                    if not self._run:
                        break
        finally:
            self._cancel_tasks()
            logger.debug("Node client shutting down")

    async def _heartbeat(self, ws: connection, state_getter) -> None:
        while self._run:
            await ws.send(dump_json(state_getter()))
            await sleep(3)

    async def _command(self, ws: connection) -> None:
        while self._run:
            message = await ws.recv()
            logger.info("Node received message: %s", message)

    def _cancel_tasks(self) -> None:
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
        if self._command_task:
            self._command_task.cancel()
            self._command_task = None

    def close(self, *args):
        self._run = False
        self._cancel_tasks()


class Inspector:
    """Inspector for Sanic workers.

    This class is used to create an inspector for Sanic workers. It is
    instantiated by the worker class and is used to create a Sanic app
    that can be used to inspect and control the workers and the server.

    It is not intended to be used directly by the user.

    See [Inspector](/en/guide/deployment/inspector) for more information.

    Args:
        publisher (Connection): The connection to the worker.
        app_info (Dict[str, Any]): Information about the app.
        worker_state (Mapping[str, Any]): The state of the worker.
        host (str): The host to bind the inspector to.
        port (int): The port to bind the inspector to.
        api_key (str): The API key to use for authentication.
        tls_key (Union[Path, str, Default]): The path to the TLS key file.
        tls_cert (Union[Path, str, Default]): The path to the TLS cert file.
    """

    def __init__(
        self,
        publisher: Connection,
        app_info: Dict[str, Any],
        worker_state: Mapping[str, Any],
        host: str,
        port: int,
        api_key: str,
        tls_key: Union[Path, str, Default],
        tls_cert: Union[Path, str, Default],
        hub_mode: Union[bool, Default] = _default,
        hub_host: str = "",
        hub_port: int = 0,
    ):
        hub_mode, node_mode = self._detect_modes(
            hub_mode, host, port, hub_host, hub_port
        )
        self._publisher = publisher
        self.app_info = app_info
        self.worker_state = worker_state
        self.host = host
        self.port = port
        self.api_key = api_key
        self.tls_key = tls_key
        self.tls_cert = tls_cert
        self.hub_mode = hub_mode
        self.node_mode = node_mode
        self.hub_host = hub_host
        self.hub_port = hub_port

    def __call__(self, run=True, **_) -> Inspector:
        from sanic import Sanic

        self.app = Sanic("Inspector")
        self._setup()
        if self.node_mode:
            run_async(self._run_node())
        elif run:
            self.app.run(
                host=self.host,
                port=self.port,
                single_process=True,
                ssl={"key": self.tls_key, "cert": self.tls_cert}
                if not isinstance(self.tls_key, Default)
                and not isinstance(self.tls_cert, Default)
                else None,
                debug=True,
            )
        return self

    def _detect_modes(
        self,
        hub_mode: Union[bool, Default],
        host: str,
        port: int,
        hub_host: str,
        hub_port: int,
    ) -> Tuple[bool, bool]:
        if hub_host == host and hub_port == port:
            if not hub_mode:
                raise ValueError(
                    "Hub mode must be enabled when using the same "
                    "host and port for the hub and the inspector"
                )
            hub_mode = True
        if (hub_host and not hub_port) or (hub_port and not hub_host):
            raise ValueError("Both hub host and hub port must be specified")
        if hub_mode is True:
            return True, False
        elif hub_host and hub_port:
            return False, True
        else:
            return False, False

    def _setup(self):
        self.app.get("/")(self._info)
        self.app.post("/<action:str>")(self._action)
        if self.api_key:
            self.app.on_request(self._authentication)
        if self.hub_mode:
            self.app.before_server_start(self._setup_hub)
            self.app.websocket("/hub")(self._hub)
        if self.node_mode:
            self.app.before_server_start(self._run_node)
        environ["SANIC_IGNORE_PRODUCTION_WARNING"] = "true"

    def _authentication(self, request: Request) -> None:
        if request.token != self.api_key:
            raise Unauthorized("Bad API key")

    async def _action(self, request: Request, action: str):
        logger.info("Incoming inspector action: %s", action)
        output: Any = None
        method = getattr(self, action, None)
        if method:
            kwargs = {}
            if request.body:
                kwargs = request.json
            args = kwargs.pop("args", ())
            output = method(*args, **kwargs)
            if isawaitable(output):
                output = await output

        return await self._respond(request, output)

    async def _info(self, request: Request):
        return await self._respond(request, self._state_to_json())

    async def _respond(self, request: Request, output: Any):
        name = request.match_info.get("action", "info")
        return json({"meta": {"action": name}, "result": output})

    def _state_to_json(self) -> Dict[str, Any]:
        output = {"info": self.app_info}
        output["workers"] = self._make_safe(dict(self.worker_state))
        if self.hub_mode:
            output["nodes"] = {
                ident: self._make_safe(asdict(node))
                for ident, node in self.app.ctx.hub_state.nodes.items()
            }
        return output

    @staticmethod
    def _make_safe(obj: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in obj.items():
            if isinstance(value, dict):
                obj[key] = Inspector._make_safe(value)
            elif isinstance(value, datetime):
                obj[key] = value.isoformat()
        return obj

    def reload(self, zero_downtime: bool = False) -> None:
        """Reload the workers

        Args:
            zero_downtime (bool, optional): Whether to use zero downtime
                reload. Defaults to `False`.
        """
        message = "__ALL_PROCESSES__:"
        if zero_downtime:
            message += ":STARTUP_FIRST"
        self._publisher.send(message)

    def scale(self, replicas: Union[str, int]) -> str:
        """Scale the number of workers

        Args:
            replicas (Union[str, int]): The number of workers to scale to.

        Returns:
            str: A log message.
        """
        num_workers = 1
        if replicas:
            num_workers = int(replicas)
        log_msg = f"Scaling to {num_workers}"
        logger.info(log_msg)
        message = f"__SCALE__:{num_workers}"
        self._publisher.send(message)
        return log_msg

    def shutdown(self) -> None:
        """Shutdown the workers"""
        message = "__TERMINATE__"
        self._publisher.send(message)

    def _setup_hub(self, app: Sanic) -> None:
        logger.info(
            f"Sanic Inspector running in hub mode on {self.host}:{self.port}"
        )
        app.ctx.hub_state = HubState(nodes={})

    async def _hub(
        self,
        request: Request,
        websocket: WebsocketImplProtocol,
    ) -> None:
        hub_state = request.app.ctx.hub_state
        ident = self._generate_ident()
        hub_state.nodes[ident] = NodeState({}, {})
        while True:
            message = await websocket.recv()
            if message == "ping":
                await websocket.send("pong")
            elif not message:
                break
            else:
                raw = load_json(message)
                node_state = NodeState(**raw)
                hub_state.nodes[ident] = node_state

    async def _run_node(self) -> None:
        client = NodeClient(self.hub_host, self.hub_port)

        def signal_close(*args, **kwargs):
            client.close()

        signal(SIGTERM, signal_close)
        signal(SIGINT, signal_close)

        logger.info(
            f"Sanic Inspector running in node mode on {self.host}:{self.port}"
        )
        await client.run(self._state_to_json)

    def _generate_ident(self, length: int = 8) -> str:
        base = ascii_lowercase + ascii_uppercase
        return "".join(random.choices(base, k=length))
