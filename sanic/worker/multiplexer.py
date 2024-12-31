from multiprocessing.connection import Connection
from os import environ, getpid
from typing import Any, Callable, Optional

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
        worker_state: dict[str, Any],
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

    def manage(
        self,
        ident: str,
        func: Callable[..., Any],
        kwargs: dict[str, Any],
        transient: bool = False,
        restartable: Optional[bool] = None,
        tracked: bool = False,
        auto_start: bool = True,
        workers: int = 1,
    ) -> None:
        """Manages the initiation and monitoring of a worker process.

        Args:
            ident (str): A unique identifier for the worker process.
            func (Callable[..., Any]): The function to be executed in the worker process.
            kwargs (Dict[str, Any]): A dictionary of arguments to be passed to `func`.
            transient (bool, optional): Flag to mark the process as transient. If `True`,
                the Worker Manager will restart the process with any global restart
                (e.g., auto-reload). Defaults to `False`.
            restartable (Optional[bool], optional): Flag to mark the process as restartable. If `True`,
                the Worker Manager can restart the process if prompted. Defaults to `None`.
            tracked (bool, optional): Flag to indicate whether the process should be tracked
                after its completion. Defaults to `False`.
            auto_start (bool, optional): Flag to indicate whether the process should be started
            workers (int, optional): The number of worker processes to run. Defaults to 1.

        This method packages the provided arguments into a bundle and sends them back to the
        main process to be managed by the Worker Manager.
        """  # noqa: E501
        bundle = (
            ident,
            func,
            kwargs,
            transient,
            restartable,
            tracked,
            auto_start,
            workers,
        )
        self._monitor_publisher.send(bundle)

    def set_serving(self, serving: bool) -> None:
        """Set the worker to serving.

        Args:
            serving (bool): Whether the worker is serving.
        """
        self._state._state[self.name] = {
            **self._state._state[self.name],
            "serving": serving,
        }

    def exit(self):
        """Run cleanup at worker exit."""
        try:
            del self._state._state[self.name]
        except ConnectionRefusedError:
            logger.debug("Monitor process has already exited.")

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
    def workers(self) -> dict[str, Any]:
        """The state of all workers."""
        return self.state.full()
