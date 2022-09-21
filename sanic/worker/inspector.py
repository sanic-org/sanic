import sys

from datetime import datetime
from multiprocessing.connection import Connection
from signal import SIGINT, SIGTERM
from signal import signal as signal_func
from socket import AF_INET, SOCK_STREAM, socket, timeout
from textwrap import indent
from typing import Any, Dict

from sanic.application.logo import get_logo
from sanic.application.motd import MOTDTTY
from sanic.log import Colors, error_logger, logger
from sanic.server.socket import configure_socket


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
    ):
        self._publisher = publisher
        self.run = True
        self.app_info = app_info
        self.worker_state = worker_state
        self.host = host
        self.port = port

    def __call__(self) -> None:
        sock = configure_socket(
            {"host": self.host, "port": self.port, "unix": None, "backlog": 1}
        )
        assert sock
        signal_func(SIGINT, self.stop)
        signal_func(SIGTERM, self.stop)

        logger.info(f"Inspector started on: {sock.getsockname()}")
        sock.settimeout(0.5)
        try:
            while self.run:
                try:
                    conn, _ = sock.accept()
                except timeout:
                    continue
                else:
                    action = conn.recv(64)
                    if action == b"reload":
                        conn.send(b"\n")
                        self.reload()
                    elif action == b"shutdown":
                        conn.send(b"\n")
                        self.shutdown()
                    else:
                        data = dumps(self.state_to_json())
                        conn.send(data.encode())
                        conn.close()
        finally:
            logger.debug("Inspector closing")
            sock.close()

    def stop(self, *_):
        self.run = False

    def state_to_json(self):
        output = {"info": self.app_info}
        output["workers"] = self.make_safe(dict(self.worker_state))
        return output

    def reload(self):
        message = "__ALL_PROCESSES__:"
        self._publisher.send(message)

    def shutdown(self):
        message = "__TERMINATE__"
        self._publisher.send(message)

    @staticmethod
    def make_safe(obj: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in obj.items():
            if isinstance(value, dict):
                obj[key] = Inspector.make_safe(value)
            elif isinstance(value, datetime):
                obj[key] = value.isoformat()
        return obj


def inspect(host: str, port: int, action: str):
    out = sys.stdout.write
    with socket(AF_INET, SOCK_STREAM) as sock:
        try:
            sock.connect((host, port))
        except ConnectionRefusedError:
            error_logger.error(
                f"{Colors.RED}Could not connect to inspector at: "
                f"{Colors.YELLOW}{(host, port)}{Colors.END}\n"
                "Either the application is not running, or it did not start "
                "an inspector instance."
            )
            sock.close()
            sys.exit(1)
        sock.sendall(action.encode())
        data = sock.recv(4096)
    if action == "raw":
        out(data.decode())
    elif action == "pretty":
        loaded = loads(data)
        display = loaded.pop("info")
        extra = display.pop("extra", {})
        display["packages"] = ", ".join(display["packages"])
        MOTDTTY(get_logo(), f"{host}:{port}", display, extra).display(
            version=False,
            action="Inspecting",
            out=out,
        )
        for name, info in loaded["workers"].items():
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
