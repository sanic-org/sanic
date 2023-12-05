from multiprocessing.connection import Connection
from os import environ, getpid
from typing import Any, Dict

from sanic.log import Colors, logger
from sanic.worker.process import ProcessState
from sanic.worker.state import WorkerState


class WorkerMultiplexer:
    """Multiplexer for Sanic workers.

    This is instantiated inside of worker porocesses only. It is used to
    communicate with the monitor process.

    Args:
        monitor_publisher (Connection): The connection to the monitor.
        worker_state (Dict[str, Any]): The state of the worker.
    """

    def __init__(
        self,
        monitor_publisher: Connection,
        worker_state: Dict[str, Any],
    ):
        self._monitor_publisher = monitor_publisher
        self._state = WorkerState(worker_state, self.name)

    def ack(self):
        """Acknowledge the worker is ready."""
        logger.debug(
            f"{Colors.BLUE}Process ack: {Colors.BOLD}{Colors.SANIC}"
            f"%s {Colors.BLUE}[%s]{Colors.END}",
            self.name,
            self.pid,
        )
        self._state._state[self.name] = {
            **self._state._state[self.name],
            "state": ProcessState.ACKED.name,
        }

    def restart(
        self,
        name: str = "",
        all_workers: bool = False,
        zero_downtime: bool = False,
    ):
        """Restart the worker.

        Args:
            name (str): The name of the process to restart.
            all_workers (bool): Whether to restart all workers.
            zero_downtime (bool): Whether to restart with zero downtime.
        """
        if name and all_workers:
            raise ValueError(
                "Ambiguous restart with both a named process and"
                " all_workers=True"
            )
        if not name:
            name = "__ALL_PROCESSES__:" if all_workers else self.name
        if not name.endswith(":"):
            name += ":"
        if zero_downtime:
            name += ":STARTUP_FIRST"
        self._monitor_publisher.send(name)

    reload = restart  # no cov
    """Alias for restart."""

    def scale(self, num_workers: int):
        """Scale the number of workers.

        Args:
            num_workers (int): The number of workers to scale to.
        """
        message = f"__SCALE__:{num_workers}"
        self._monitor_publisher.send(message)

    def terminate(self, early: bool = False):
        """Terminate the worker.

        Args:
            early (bool): Whether to terminate early.
        """
        message = "__TERMINATE_EARLY__" if early else "__TERMINATE__"
        self._monitor_publisher.send(message)

    @property
    def pid(self) -> int:
        """The process ID of the worker."""
        return getpid()

    @property
    def name(self) -> str:
        """The name of the worker."""
        return environ.get("SANIC_WORKER_NAME", "")

    @property
    def state(self):
        """The state of the worker."""
        return self._state

    @property
    def workers(self) -> Dict[str, Any]:
        """The state of all workers."""
        return self.state.full()
