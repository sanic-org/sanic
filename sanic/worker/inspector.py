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
        return json(
            {"meta": {"action": name}, "result": output},
            escape_forward_slashes=False,
        )

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
        message = "__ALL_PROCESSES__:"
        if zero_downtime:
            message += ":STARTUP_FIRST"
        self._publisher.send(message)

    def scale(self, replicas) -> str:
        num_workers = 1
        if replicas:
            num_workers = int(replicas)
        log_msg = f"Scaling to {num_workers}"
        logger.info(log_msg)
        message = f"__SCALE__:{num_workers}"
        self._publisher.send(message)
        return log_msg

    def shutdown(self) -> None:
        message = "__TERMINATE__"
        self._publisher.send(message)
