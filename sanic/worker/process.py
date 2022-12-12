import os

from datetime import datetime, timezone
from enum import IntEnum, auto
from multiprocessing.context import BaseContext
from signal import SIGINT
from threading import Thread
from typing import Any, Dict, Set

from sanic.constants import RestartOrder
from sanic.log import Colors, logger


def get_now():
    now = datetime.now(tz=timezone.utc)
    return now


class ProcessState(IntEnum):
    IDLE = auto()
    RESTARTING = auto()
    STARTING = auto()
    STARTED = auto()
    ACKED = auto()
    JOINED = auto()
    TERMINATED = auto()


class WorkerProcess:
    SERVER_LABEL = "Server"

    def __init__(
        self,
        factory,
        name,
        target,
        kwargs,
        worker_state,
        restart_order: RestartOrder,
    ):
        self.state = ProcessState.IDLE
        self.factory = factory
        self.name = name
        self.target = target
        self.kwargs = kwargs
        self.worker_state = worker_state
        self.restart_order = restart_order
        if self.name not in self.worker_state:
            self.worker_state[self.name] = {
                "server": self.SERVER_LABEL in self.name
            }
        self.spawn()

    def set_state(self, state: ProcessState, force=False):
        if not force and state < self.state:
            raise Exception("...")
        self.state = state
        self.worker_state[self.name] = {
            **self.worker_state[self.name],
            "state": self.state.name,
        }

    def start(self):
        os.environ["SANIC_WORKER_NAME"] = self.name
        logger.debug(
            f"{Colors.BLUE}Starting a process: {Colors.BOLD}"
            f"{Colors.SANIC}%s{Colors.END}",
            self.name,
        )
        self.set_state(ProcessState.STARTING)
        self._current_process.start()
        self.set_state(ProcessState.STARTED)
        if not self.worker_state[self.name].get("starts"):
            self.worker_state[self.name] = {
                **self.worker_state[self.name],
                "pid": self.pid,
                "start_at": get_now(),
                "starts": 1,
            }
        del os.environ["SANIC_WORKER_NAME"]

    def join(self):
        self.set_state(ProcessState.JOINED)
        self._current_process.join()

    def terminate(self):
        if self.state is not ProcessState.TERMINATED:
            logger.debug(
                f"{Colors.BLUE}Terminating a process: "
                f"{Colors.BOLD}{Colors.SANIC}"
                f"%s {Colors.BLUE}[%s]{Colors.END}",
                self.name,
                self.pid,
            )
            self.set_state(ProcessState.TERMINATED, force=True)
            try:
                os.kill(self.pid, SIGINT)
                del self.worker_state[self.name]
            except (KeyError, AttributeError, ProcessLookupError):
                ...

    def restart(self, **kwargs):
        logger.debug(
            f"{Colors.BLUE}Restarting a process: {Colors.BOLD}{Colors.SANIC}"
            f"%s {Colors.BLUE}[%s]{Colors.END}",
            self.name,
            self.pid,
        )
        self.set_state(ProcessState.RESTARTING, force=True)
        if self.restart_order is RestartOrder.SHUTDOWN_FIRST:
            self._terminate_now()
        else:
            self._old_process = self._current_process
        self.kwargs.update(
            {"config": {k.upper(): v for k, v in kwargs.items()}}
        )
        try:
            self.spawn()
            self.start()
        except AttributeError:
            raise RuntimeError("Restart failed")

        if self.restart_order is RestartOrder.STARTUP_FIRST:
            self._terminate_soon()

        self.worker_state[self.name] = {
            **self.worker_state[self.name],
            "pid": self.pid,
            "starts": self.worker_state[self.name]["starts"] + 1,
            "restart_at": get_now(),
        }

    def _terminate_now(self):
        logger.debug(
            f"{Colors.BLUE}Begin restart termination: "
            f"{Colors.BOLD}{Colors.SANIC}"
            f"%s {Colors.BLUE}[%s]{Colors.END}",
            self.name,
            self._current_process.pid,
        )
        self._current_process.terminate()

    def _terminate_soon(self):
        logger.debug(
            f"{Colors.BLUE}Begin restart termination: "
            f"{Colors.BOLD}{Colors.SANIC}"
            f"%s {Colors.BLUE}[%s]{Colors.END}",
            self.name,
            self._current_process.pid,
        )
        termination_thread = Thread(target=self._wait_to_terminate)
        termination_thread.start()

    def _wait_to_terminate(self):
        # TODO: Add a timeout?
        while self.state is not ProcessState.ACKED:
            ...
        else:
            logger.debug(
                f"{Colors.BLUE}Process acked. Terminating: "
                f"{Colors.BOLD}{Colors.SANIC}"
                f"%s {Colors.BLUE}[%s]{Colors.END}",
                self.name,
                self._old_process.pid,
            )
            self._old_process.terminate()
        delattr(self, "_old_process")

    def is_alive(self):
        try:
            return self._current_process.is_alive()
        except AssertionError:
            return False

    def spawn(self):
        if self.state not in (ProcessState.IDLE, ProcessState.RESTARTING):
            raise Exception("Cannot spawn a worker process until it is idle.")
        self._current_process = self.factory(
            name=self.name,
            target=self.target,
            kwargs=self.kwargs,
            daemon=True,
        )

    @property
    def pid(self):
        return self._current_process.pid


class Worker:
    WORKER_PREFIX = "SANIC-"

    def __init__(
        self,
        ident: str,
        serve,
        server_settings,
        context: BaseContext,
        worker_state: Dict[str, Any],
        restart_order: RestartOrder,
    ):
        self.ident = f"{self.WORKER_PREFIX}{ident}"
        self.context = context
        self.serve = serve
        self.server_settings = server_settings
        self.worker_state = worker_state
        self.processes: Set[WorkerProcess] = set()
        self.restart_order = restart_order
        self.create_process()

    def create_process(self) -> WorkerProcess:
        process = WorkerProcess(
            factory=self.context.Process,
            name=f"{self.ident}-{len(self.processes)}",
            target=self.serve,
            kwargs={**self.server_settings},
            worker_state=self.worker_state,
            restart_order=self.restart_order,
        )
        self.processes.add(process)
        return process
