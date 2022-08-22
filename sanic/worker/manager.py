import os

from signal import SIGINT, SIGKILL, SIGTERM, Signals
from signal import signal as signal_func
from time import sleep
from typing import List, Optional

from sanic.log import logger
from sanic.worker.process import ProcessState, Worker


class WorkerManager:
    def __init__(
        self,
        number: int,
        serve,
        server_settings,
        context,
        monitor_pubsub,
        worker_state,
    ):
        self.context = context
        self.transient: List[Worker] = []
        self.durable: List[Worker] = []
        self.monitor_publisher, self.monitor_subscriber = monitor_pubsub
        self.worker_state = worker_state
        self.worker_state["Sanic-Main"] = {"pid": self.pid}
        self.terminated = False

        if number == 0:
            raise RuntimeError("Cannot serve with no workers")

        for i in range(number):
            self.manage(f"Worker-{i}", serve, server_settings, transient=True)

        signal_func(SIGINT, self.shutdown_signal)
        signal_func(SIGTERM, self.shutdown_signal)

    def manage(self, ident, func, kwargs, transient=False):
        container = self.transient if transient else self.durable
        container.append(
            Worker(ident, func, kwargs, self.context, self.worker_state)
        )

    def run(self):
        self.start()
        self.monitor()
        self.join()
        self.terminate()
        # self.kill()

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
        if not self.terminated:
            for process in self.processes:
                process.terminate()
        self.terminated = True

    def restart(self, process_names: Optional[List[str]] = None, **kwargs):
        for process in self.transient_processes:
            if not process_names or process.name in process_names:
                process.restart(**kwargs)

    def monitor(self):
        sleep(1)
        while True:
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
                split_message = message.split(":", 1)
                processes = split_message[0]
                reloaded_files = (
                    split_message[1] if len(split_message) > 1 else None
                )
                process_names = [name.strip() for name in processes.split(",")]
                if "__ALL_PROCESSES__" in process_names:
                    process_names = None
                self.restart(
                    process_names=process_names, reloaded_files=reloaded_files
                )

    @property
    def workers(self):
        return self.transient + self.durable

    @property
    def processes(self):
        for worker in self.workers:
            for process in worker.processes:
                yield process

    @property
    def transient_processes(self):
        for worker in self.transient:
            for process in worker.processes:
                yield process

    def kill(self):
        for process in self.processes:
            os.kill(process.pid, SIGKILL)

    def shutdown_signal(self, signal, frame):
        logger.info("Received signal %s. Shutting down.", Signals(signal).name)
        self.monitor_publisher.send(None)
        self.shutdown()

    def shutdown(self):
        for process in self.processes:
            if process.is_alive():
                process.terminate()

    @property
    def pid(self):
        return os.getpid()
