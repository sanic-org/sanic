from __future__ import annotations

from datetime import datetime
from inspect import isawaitable
from multiprocessing.connection import Connection
from os import environ
from pathlib import Path
from typing import Any, Dict, Mapping, Union

from sanic.exceptions import Unauthorized
from sanic.helpers import Default
from sanic.log import logger
from sanic.request import Request
from sanic.response import json


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
    ):
        self._publisher = publisher
        self.app_info = app_info
        self.worker_state = worker_state
        self.host = host
        self.port = port
        self.api_key = api_key
        self.tls_key = tls_key
        self.tls_cert = tls_cert

    def __call__(self, run=True, **_) -> Inspector:
        from sanic import Sanic

        self.app = Sanic("Inspector")
        self._setup()
        if run:
            self.app.run(
                host=self.host,
                port=self.port,
                single_process=True,
                ssl={"key": self.tls_key, "cert": self.tls_cert}
                if not isinstance(self.tls_key, Default)
                and not isinstance(self.tls_cert, Default)
                else None,
            )
        return self

    def _setup(self):
        self.app.get("/")(self._info)
        self.app.post("/<action:str>")(self._action)
        if self.api_key:
            self.app.on_request(self._authentication)
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
