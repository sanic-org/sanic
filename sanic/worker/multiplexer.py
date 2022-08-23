from multiprocessing.connection import Connection
from os import environ, getpid
from typing import Any, Dict

from sanic.worker.process import ProcessState


class WorkerMultiplexer:
    def __init__(
        self,
        monitor_publisher: Connection,
        worker_state: Dict[str, Any],
    ):
        self._monitor_publisher = monitor_publisher
        self._worker_state = worker_state
        self._worker_state[self.name] = {
            **self._worker_state[self.name],
            "state": ProcessState.ACKED.name,
            "server": True,
        }

    def restart(self, name: str = ""):
        if not name:
            name = self.name
        self._monitor_publisher.send(name)

    def terminate(self):
        self._monitor_publisher.send("__TERMINATE__")

    @property
    def pid(self) -> int:
        return getpid()

    @property
    def name(self) -> str:
        return environ.get("SANIC_WORKER_NAME", "")

    @property
    def workers(self) -> Dict[str, Any]:
        return self._worker_state
