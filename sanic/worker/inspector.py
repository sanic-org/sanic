import sys

from datetime import datetime
from http.client import RemoteDisconnected
from inspect import isawaitable
from multiprocessing.connection import Connection
from os import environ
from pathlib import Path
from textwrap import indent
from typing import Any, Dict, Union
from urllib.error import URLError
from urllib.request import Request as URequest
from urllib.request import urlopen

from sanic.application.logo import get_logo
from sanic.application.motd import MOTDTTY
from sanic.helpers import Default
from sanic.log import Colors, logger
from sanic.request import Request
from sanic.response import json


try:  # no cov
    from ujson import dumps, loads
except ModuleNotFoundError:  # no cov
    from json import dumps, loads  # type: ignore


class Inspector:
    def __init__(
        self,
        publisher: Connection,
        app_info: Dict[str, Any],
        worker_state: Dict[str, Any],
        host: str,
        port: int,
        tls_key: Union[Path, str, Default],
        tls_cert: Union[Path, str, Default],
    ):
        self._publisher = publisher
        self.run = True
        self.app_info = app_info
        self.worker_state = worker_state
        self.host = host
        self.port = port
        self.tls_key = tls_key
        self.tls_cert = tls_cert

    def __call__(self, **_) -> None:
        from sanic import Sanic

        self.app = Sanic("Inspector")
        self._setup()
        self.app.run(
            host=self.host,
            port=self.port,
            single_process=True,
            ssl={"key": self.tls_key, "cert": self.tls_cert}
            if not isinstance(self.tls_key, Default)
            and not isinstance(self.tls_cert, Default)
            else None,
        )

    def _setup(self):
        self.app.get("/")(self._info)
        self.app.post("/<action:str>")(self._action)
        environ["SANIC_IGNORE_PRODUCTION_WARNING"] = "true"

    async def _action(self, request: Request, action: str):
        logger.info("Incoming inspector action: %s", action)
        output: Any = None
        method = getattr(self, action, None)
        if method:
            kwargs = {}
            if request.body:
                kwargs = request.json
            output = method(**kwargs)
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

    def reload(self) -> None:
        message = "__ALL_PROCESSES__:"
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


class InspectorClient:
    def __init__(self, host: str, port: int, secure: bool, raw: bool) -> None:
        self.scheme = "https" if secure else "http"
        self.host = host
        self.port = port
        self.raw = raw

        for scheme in ("http", "https"):
            full = f"{scheme}://"
            if self.host.startswith(full):
                self.scheme = scheme
                self.host = self.host[len(full) :]  # noqa E203

    def do(self, action: str, **kwargs: Any) -> None:
        if action == "info":
            self.info()
            return
        result = self.request(action, **kwargs).get("result")
        if result:
            out = (
                dumps(result)
                if isinstance(result, (list, dict))
                else str(result)
            )
            sys.stdout.write(out + "\n")

    def info(self) -> None:
        out = sys.stdout.write
        response = self.request("", "GET")
        if self.raw:
            return
        data = response["result"]
        display = data.pop("info")
        extra = display.pop("extra", {})
        display["packages"] = ", ".join(display["packages"])
        MOTDTTY(get_logo(), self.base_url, display, extra).display(
            version=False,
            action="Inspecting",
            out=out,
        )
        for name, info in data["workers"].items():
            info = "\n".join(
                f"\t{key}: {Colors.BLUE}{value}{Colors.END}"
                for key, value in info.items()
            )
            out(
                "\n"
                + indent(
                    "\n".join(
                        [
                            f"{Colors.BOLD}{Colors.SANIC}{name}{Colors.END}",
                            info,
                        ]
                    ),
                    "  ",
                )
                + "\n"
            )

    def request(self, action: str, method: str = "POST", **kwargs: Any) -> Any:
        url = f"{self.base_url}/{action}"
        params = {"method": method}
        if kwargs:
            params["data"] = dumps(kwargs).encode()
            params["headers"] = {"content-type": "application/json"}
        request = URequest(url, **params)

        try:
            with urlopen(request) as response:  # nosec B310
                raw = response.read()
                loaded = loads(raw)
                if self.raw:
                    sys.stdout.write(dumps(loaded.get("result")) + "\n")
                    return {}
                return loaded
        except (URLError, RemoteDisconnected) as e:
            sys.stderr.write(
                f"{Colors.RED}Could not connect to inspector at: "
                f"{Colors.YELLOW}{self.base_url}{Colors.END}\n"
                "Either the application is not running, or it did not start "
                f"an inspector instance.\n{e}\n"
            )
            sys.exit(1)

    @property
    def base_url(self):
        return f"{self.scheme}://{self.host}:{self.port}"
