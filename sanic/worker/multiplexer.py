from multiprocessing.connection import Connection
from os import environ, getpid
from typing import Any, Dict

from sanic.worker.process import ProcessState
from sanic.worker.state import WorkerState


class WorkerMultiplexer:
    def __init__(
        self,
        monitor_publisher: Connection,
        worker_state: Dict[str, Any],
    ):
        self._monitor_publisher = monitor_publisher
        self._state = WorkerState(worker_state, self.name)

    def ack(self):
        self._state._state[self.name] = {
            **self._state._state[self.name],
            "state": ProcessState.ACKED.name,
        }

    def restart(self, name: str = "", all_workers: bool = False):
        if name and all_workers:
            raise ValueError(
                "Ambiguous restart with both a named process and"
                " all_workers=True"
            )
        if not name:
            name = "__ALL_PROCESSES__:" if all_workers else self.name
        self._monitor_publisher.send(name)

    reload = restart  # no cov

    def terminate(self, early: bool = False):
        message = "__TERMINATE_EARLY__" if early else "__TERMINATE__"
        self._monitor_publisher.send(message)

    @property
    def pid(self) -> int:
        return getpid()

    @property
    def name(self) -> str:
        return environ.get("SANIC_WORKER_NAME", "")

    @property
    def state(self):
        return self._state

    @property
    def workers(self) -> Dict[str, Any]:
        return self.state.full()
