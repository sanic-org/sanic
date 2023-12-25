from typing import List, Optional, Set

from sanic.log import error_logger
from sanic.worker.constants import RestartOrder
from sanic.worker.process import ProcessState, WorkerProcess


class Restarter:
    def restart(
        self,
        transient_processes: List[WorkerProcess],
        durable_processes: List[WorkerProcess],
        process_names: Optional[List[str]] = None,
        restart_order=RestartOrder.SHUTDOWN_FIRST,
        **kwargs,
    ) -> None:
        """Restart the worker processes.

        Args:
            process_names (Optional[List[str]], optional): The names of the processes to restart.
                If `None`, then all processes will be restarted. Defaults to `None`.
            restart_order (RestartOrder, optional): The order in which to restart the processes.
                Defaults to `RestartOrder.SHUTDOWN_FIRST`.
        """  # noqa: E501
        restarted = self._restart_transient(
            transient_processes,
            process_names or [],
            restart_order,
            **kwargs,
        )
        restarted |= self._restart_durable(
            durable_processes,
            process_names or [],
            restart_order,
            **kwargs,
        )

        if process_names and not restarted:
            error_logger.error(
                f"Failed to restart processes: {', '.join(process_names)}"
            )

    def _restart_transient(
        self,
        processes: List[WorkerProcess],
        process_names: List[str],
        restart_order: RestartOrder,
        **kwargs,
    ) -> Set[str]:
        restarted: Set[str] = set()
        for process in processes:
            if not process.restartable or (
                process_names and process.name not in process_names
            ):
                continue
            self._restart_process(process, restart_order, **kwargs)
            restarted.add(process.name)
        return restarted

    def _restart_durable(
        self,
        processes: List[WorkerProcess],
        process_names: List[str],
        restart_order: RestartOrder,
        **kwargs,
    ) -> Set[str]:
        restarted: Set[str] = set()
        if not process_names:
            return restarted
        for process in processes:
            if not process.restartable or process.name not in process_names:
                continue
            if process.state not in (
                ProcessState.COMPLETED,
                ProcessState.FAILED,
                ProcessState.NONE,
            ):
                error_logger.error(
                    f"Cannot restart process {process.name} because "
                    "it is not in a final state. Current state is: "
                    f"{process.state.name}."
                )
                continue
            self._restart_process(process, restart_order, **kwargs)
            restarted.add(process.name)

        return restarted

    def _restart_process(self, process, restart_order, **kwargs):
        process.restart(restart_order=restart_order, **kwargs)
