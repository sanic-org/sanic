from __future__ import annotations

import sys

from http.client import RemoteDisconnected
from textwrap import indent
from typing import Any, Dict, Optional
from urllib.error import URLError
from urllib.request import Request as URequest
from urllib.request import urlopen

from sanic.application.logo import get_logo
from sanic.application.motd import MOTDTTY
from sanic.log import Colors


try:  # no cov
    from ujson import dumps, loads
except ModuleNotFoundError:  # no cov
    from json import dumps, loads  # type: ignore


class InspectorClient:
    def __init__(
        self,
        host: str,
        port: int,
        secure: bool,
        raw: bool,
        api_key: Optional[str],
    ) -> None:
        self.scheme = "https" if secure else "http"
        self.host = host
        self.port = port
        self.raw = raw
        self.api_key = api_key

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
        if self.raw or not response:
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
        params: Dict[str, Any] = {"method": method, "headers": {}}
        if kwargs:
            params["data"] = dumps(kwargs).encode()
            params["headers"]["content-type"] = "application/json"
        if self.api_key:
            params["headers"]["authorization"] = f"Bearer {self.api_key}"
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
