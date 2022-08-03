from multiprocessing.connection import Connection
from os import environ, getpid
from typing import Any, Dict


class WorkerMultiplexer:
    def __init__(
        self,
        restart_publisher: Connection,
        worker_state: Dict[str, Any],
    ):
        self._restart_publisher = restart_publisher
        self._worker_state = worker_state

    def restart(self):
        self._restart_publisher.send(True)

    @property
    def pid(self) -> int:
        return getpid()

    @property
    def name(self) -> str:
        return environ.get("SANIC_WORKER_PROCESS", "")

    @property
    def workers(self) -> Dict[str, Any]:
        return self._worker_state
