import os

from contextlib import suppress
from itertools import count
from random import choice
from signal import SIGINT, SIGTERM, Signals
from signal import signal as signal_func
from typing import Dict, List, Optional

from sanic.compat import OS_IS_WINDOWS
from sanic.exceptions import ServerKilled
from sanic.log import error_logger, logger
from sanic.worker.constants import RestartOrder
from sanic.worker.process import ProcessState, Worker, WorkerProcess


if not OS_IS_WINDOWS:
    from signal import SIGKILL
else:
    SIGKILL = SIGINT


class WorkerManager:
    THRESHOLD = WorkerProcess.THRESHOLD
    MAIN_IDENT = "Sanic-Main"

    def __init__(
        self,
        number: int,
        serve,
        server_settings,
        context,
        monitor_pubsub,
        worker_state,
    ):
        self.num_server = number
        self.context = context
        self.transient: Dict[str, Worker] = {}
        self.durable: Dict[str, Worker] = {}
        self.monitor_publisher, self.monitor_subscriber = monitor_pubsub
        self.worker_state = worker_state
        self.worker_state[self.MAIN_IDENT] = {"pid": self.pid}
        self._shutting_down = False
        self._serve = serve
        self._server_settings = server_settings
        self._server_count = count()

        if number == 0:
            raise RuntimeError("Cannot serve with no workers")

        for _ in range(number):
            self.create_server()

        signal_func(SIGINT, self.shutdown_signal)
        signal_func(SIGTERM, self.shutdown_signal)

    def manage(self, ident, func, kwargs, transient=False) -> Worker:
        container = self.transient if transient else self.durable
        worker = Worker(ident, func, kwargs, self.context, self.worker_state)
        container[worker.ident] = worker
        return worker

    def create_server(self) -> Worker:
        server_number = next(self._server_count)
        return self.manage(
            f"{WorkerProcess.SERVER_LABEL}-{server_number}",
            self._serve,
            self._server_settings,
            transient=True,
        )

    def shutdown_server(self, ident: Optional[str] = None) -> None:
        if not ident:
            servers = [
                worker
                for worker in self.transient.values()
                if worker.ident.startswith(WorkerProcess.SERVER_LABEL)
            ]
            if not servers:
                error_logger.error(
                    "Server shutdown failed because a server was not found."
                )
                return
            worker = choice(servers)  # nosec B311
        else:
            worker = self.transient[ident]

        for process in worker.processes:
            process.terminate()

        del self.transient[worker.ident]

    def run(self):
        self.start()
        self.monitor()
        self.join()
        self.terminate()

    def start(self):
        for process in self.processes:
            process.start()

    def join(self):
        logger.debug("Joining processes", extra={"verbosity": 1})
        joined = set()
        for process in self.processes:
            logger.debug(
                f"Found {process.pid} - {process.state.name}",
                extra={"verbosity": 1},
            )
            if process.state < ProcessState.JOINED:
                logger.debug(f"Joining {process.pid}", extra={"verbosity": 1})
                joined.add(process.pid)
                process.join()
        if joined:
            self.join()

    def terminate(self):
        if not self._shutting_down:
            for process in self.processes:
                process.terminate()

    def restart(
        self,
        process_names: Optional[List[str]] = None,
        restart_order=RestartOrder.SHUTDOWN_FIRST,
        **kwargs,
    ):
        for process in self.transient_processes:
            if not process_names or process.name in process_names:
                process.restart(restart_order=restart_order, **kwargs)

    def scale(self, num_worker: int):
        if num_worker <= 0:
            raise ValueError("Cannot scale to 0 workers.")

        change = num_worker - self.num_server
        if change == 0:
            logger.info(
                f"No change needed. There are already {num_worker} workers."
            )
            return

        logger.info(f"Scaling from {self.num_server} to {num_worker} workers")
        if change > 0:
            for _ in range(change):
                worker = self.create_server()
                for process in worker.processes:
                    process.start()
        else:
            for _ in range(abs(change)):
                self.shutdown_server()
        self.num_server = num_worker

    def monitor(self):
        self.wait_for_ack()
        while True:
            try:
                if self.monitor_subscriber.poll(0.1):
                    message = self.monitor_subscriber.recv()
                    logger.debug(
                        f"Monitor message: {message}", extra={"verbosity": 2}
                    )
                    if not message:
                        break
                    elif message == "__TERMINATE__":
                        self.shutdown()
                        break
                    logger.debug(
                        "Incoming monitor message: %s",
                        message,
                        extra={"verbosity": 1},
                    )
                    split_message = message.split(":", 2)
                    if message.startswith("__SCALE__"):
                        self.scale(int(split_message[-1]))
                        continue
                    processes = split_message[0]
                    reloaded_files = (
                        split_message[1] if len(split_message) > 1 else None
                    )
                    process_names = [
                        name.strip() for name in processes.split(",")
                    ]
                    if "__ALL_PROCESSES__" in process_names:
                        process_names = None
                    order = (
                        RestartOrder.STARTUP_FIRST
                        if "STARTUP_FIRST" in split_message
                        else RestartOrder.SHUTDOWN_FIRST
                    )
                    self.restart(
                        process_names=process_names,
                        reloaded_files=reloaded_files,
                        restart_order=order,
                    )
                self._sync_states()
            except InterruptedError:
                if not OS_IS_WINDOWS:
                    raise
                break

    def wait_for_ack(self):  # no cov
        misses = 0
        message = (
            "It seems that one or more of your workers failed to come "
            "online in the allowed time. Sanic is shutting down to avoid a "
            f"deadlock. The current threshold is {self.THRESHOLD / 10}s. "
            "If this problem persists, please check out the documentation "
            "https://sanic.dev/en/guide/deployment/manager.html#worker-ack."
        )
        while not self._all_workers_ack():
            if self.monitor_subscriber.poll(0.1):
                monitor_msg = self.monitor_subscriber.recv()
                if monitor_msg != "__TERMINATE_EARLY__":
                    self.monitor_publisher.send(monitor_msg)
                    continue
                misses = self.THRESHOLD
                message = (
                    "One of your worker processes terminated before startup "
                    "was completed. Please solve any errors experienced "
                    "during startup. If you do not see an exception traceback "
                    "in your error logs, try running Sanic in in a single "
                    "process using --single-process or single_process=True. "
                    "Once you are confident that the server is able to start "
                    "without errors you can switch back to multiprocess mode."
                )
            misses += 1
            if misses > self.THRESHOLD:
                error_logger.error(
                    "Not all workers acknowledged a successful startup. "
                    "Shutting down.\n\n" + message
                )
                self.kill()

    @property
    def workers(self) -> List[Worker]:
        return list(self.transient.values()) + list(self.durable.values())

    @property
    def processes(self):
        for worker in self.workers:
            for process in worker.processes:
                yield process

    @property
    def transient_processes(self):
        for worker in self.transient.values():
            for process in worker.processes:
                yield process

    def kill(self):
        for process in self.processes:
            logger.info("Killing %s [%s]", process.name, process.pid)
            os.kill(process.pid, SIGKILL)
        raise ServerKilled

    def shutdown_signal(self, signal, frame):
        if self._shutting_down:
            logger.info("Shutdown interrupted. Killing.")
            with suppress(ServerKilled):
                self.kill()

        logger.info("Received signal %s. Shutting down.", Signals(signal).name)
        self.monitor_publisher.send(None)
        self.shutdown()

    def shutdown(self):
        for process in self.processes:
            if process.is_alive():
                process.terminate()
        self._shutting_down = True

    @property
    def pid(self):
        return os.getpid()

    def _all_workers_ack(self):
        acked = [
            worker_state.get("state") == ProcessState.ACKED.name
            for worker_state in self.worker_state.values()
            if worker_state.get("server")
        ]
        return all(acked) and len(acked) == self.num_server

    def _sync_states(self):
        for process in self.processes:
            state = self.worker_state[process.name].get("state")
            if state and process.state.name != state:
                process.set_state(ProcessState[state], True)
