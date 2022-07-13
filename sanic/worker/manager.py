import os

from signal import SIG_IGN, SIGINT, SIGTERM, Signals
from signal import signal as signal_func
from time import sleep

from sanic.log import logger
from sanic.worker.process import ProcessState, Worker


def fake_serve(**kwargs):
    run = True
    logger.info(kwargs)

    def stop(*_):
        nonlocal run
        run = False

    pid = os.getpid()
    n = 0
    signal_func(SIGINT, SIG_IGN)
    signal_func(SIGTERM, stop)

    while run:
        n += 1
        logger.info(pid)
        sleep(1)


class WorkerManager:
    def __init__(self, number: int, serve, server_settings, context):
        self.workers = [
            Worker(i, serve, server_settings, context) for i in range(number)
        ]
        self.monitoring = False
        signal_func(SIGINT, self.kill)
        signal_func(SIGTERM, self.kill)

    def run(self):
        self.start()
        # self.monitor()
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
        for process in self.processes:
            process.terminate()

    # def monitor(self):
    #     self.monitoring = True
    #     while self.monitoring:
    #         for worker in self.workers:
    #             worker.check()

    @property
    def processes(self):
        for worker in self.workers:
            for process in worker.processes:
                yield process

    def kill(self, signal, frame):
        self.monitoring = False
        logger.info("Received signal %s. Shutting down.", Signals(signal).name)
        for process in self.processes:
            if process.is_alive():
                os.kill(process.pid, SIGTERM)

    @property
    def pid(self):
        return os.getpid()
