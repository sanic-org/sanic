import os

from datetime import datetime, timezone
from multiprocessing.context import BaseContext
from signal import SIGINT
from threading import Thread
from time import sleep
from typing import Any, Dict, Set

from sanic.log import Colors, logger
from sanic.worker.constants import ProcessState, RestartOrder


def get_now():
    now = datetime.now(tz=timezone.utc)
    return now


class WorkerProcess:
    THRESHOLD = 300  # == 30 seconds
    SERVER_LABEL = "Server"

    def __init__(self, factory, name, target, kwargs, worker_state):
        self.state = ProcessState.IDLE
        self.factory = factory
        self.name = name
        self.target = target
        self.kwargs = kwargs
        self.worker_state = worker_state
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

    def restart(self, restart_order=RestartOrder.SHUTDOWN_FIRST, **kwargs):
        logger.debug(
            f"{Colors.BLUE}Restarting a process: {Colors.BOLD}{Colors.SANIC}"
            f"%s {Colors.BLUE}[%s]{Colors.END}",
            self.name,
            self.pid,
        )
        self.set_state(ProcessState.RESTARTING, force=True)
        if restart_order is RestartOrder.SHUTDOWN_FIRST:
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

        if restart_order is RestartOrder.STARTUP_FIRST:
            self._terminate_soon()

        self.worker_state[self.name] = {
            **self.worker_state[self.name],
            "pid": self.pid,
            "starts": self.worker_state[self.name]["starts"] + 1,
            "restart_at": get_now(),
        }

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
        logger.debug(
            f"{Colors.BLUE}Waiting for process to be acked: "
            f"{Colors.BOLD}{Colors.SANIC}"
            f"%s {Colors.BLUE}[%s]{Colors.END}",
            self.name,
            self._old_process.pid,
        )
        misses = 0
        while self.state is not ProcessState.ACKED:
            sleep(0.1)
            misses += 1
            if misses > self.THRESHOLD:
                raise TimeoutError(
                    f"Worker {self.name} failed to come ack within "
                    f"{self.THRESHOLD / 10} seconds"
                )
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


class Worker:
    WORKER_PREFIX = "Sanic-"

    def __init__(
        self,
        ident: str,
        serve,
        server_settings,
        context: BaseContext,
        worker_state: Dict[str, Any],
    ):
        self.ident = ident
        self.context = context
        self.serve = serve
        self.server_settings = server_settings
        self.worker_state = worker_state
        self.processes: Set[WorkerProcess] = set()
        self.create_process()

    def create_process(self) -> WorkerProcess:
        process = WorkerProcess(
            # Need to ignore this typing error - The problem is the
            # BaseContext itself has no Process. But, all of its
            # implementations do. We can safely ignore as it is a typing
            # issue in the standard lib.
            factory=self.context.Process,  # type: ignore
            name=f"{self.WORKER_PREFIX}{self.ident}-{len(self.processes)}",
            target=self.serve,
            kwargs={**self.server_settings},
            worker_state=self.worker_state,
        )
        self.processes.add(process)
        return process
