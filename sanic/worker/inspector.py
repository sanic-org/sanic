import sys

from datetime import datetime
from signal import SIGINT, SIGTERM
from signal import signal as signal_func
from socket import AF_INET, SOCK_STREAM, socket, timeout
from typing import Any, Dict

from sanic.log import Colors, error_logger, logger
from sanic.server.socket import configure_socket


try:
    from ujson import dumps, loads
except ModuleNotFoundError:
    from json import dumps, loads  # type: ignore


class Inspector:
    def __init__(self, worker_state: Dict[str, Any], host: str, port: int):
        self.run = True
        self.worker_state = worker_state
        self.host = host
        self.port = port

    def __call__(self) -> None:
        sock = configure_socket(
            {"host": self.host, "port": self.port, "unix": None, "backlog": 1}
        )
        signal_func(SIGINT, self.stop)
        signal_func(SIGTERM, self.stop)

        logger.info(f"Inspector started on: {sock.getsockname()}")
        sock.settimeout(0.5)
        while self.run:
            try:
                conn, _ = sock.accept()
            except timeout:
                ...
            else:
                data = dumps(self.state_to_json())
                conn.send(data.encode())
                conn.close()

        logger.info(dumps(self.state_to_json()))
        logger.debug("Inspector closing")
        sock.close()

    def stop(self, *_):
        self.run = False

    def state_to_json(self):
        return self._make_safe(dict(self.worker_state))

    def _make_safe(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in obj.items():
            if isinstance(value, dict):
                obj[key] = self._make_safe(value)
            elif isinstance(value, datetime):
                obj[key] = value.isoformat()
        return obj


def inspect(host: str, port: int):
    logger.info(f"Inspecting on {Colors.YELLOW}{(host, port)}{Colors.END}")
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
            sys.exit(1)
        data = sock.recv(4096)
    loaded = loads(data)
    output = "\n" + dumps(loaded, indent=4)
    logger.info(output)
