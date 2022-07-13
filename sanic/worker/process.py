from enum import IntEnum, auto
from multiprocessing.context import BaseContext

# from multiprocessing import Queue
from typing import Set

from sanic.log import logger


class ProcessState(IntEnum):
    IDLE = auto()
    STARTED = auto()
    JOINED = auto()
    TERMINATED = auto()


class WorkerProcess:
    def __init__(self, factory, name, target, kwargs):
        self.state = ProcessState.IDLE
        # self.misses = 0
        self.factory = factory
        self.name = name
        self.target = target
        self.kwargs = kwargs
        self.spawn()

    def set_state(self, state: ProcessState, force=False):
        if not force and state < self.state:
            raise Exception("...")
        self.state = state

    def start(self):
        logger.debug("Starting a process: %s", self.name)
        self.set_state(ProcessState.STARTED)
        self._process.start()

    def join(self):
        self.set_state(ProcessState.JOINED)
        self._process.join()

    def terminate(self):
        logger.debug("Terminating a process: %s [%s]", self.name, self.pid)
        self.set_state(ProcessState.TERMINATED, force=True)
        self._process.terminate()

    def restart(self):
        logger.debug("Restarting a process: %s [%s]", self.name, self.pid)
        self._process.terminate()
        self.set_state(ProcessState.IDLE, force=True)
        self.spawn()
        self.start()

    def is_alive(self):
        return self._process.is_alive()

    def spawn(self):
        if self.state is not ProcessState.IDLE:
            raise Exception("Cannot spawn a worker process until it is idle.")
        self._process = self.factory(
            name=self.name,
            target=self.target,
            kwargs=self.kwargs,
        )
        self._process.daemon = True

    # def missed(self):
    #     self.misses += 1

    @property
    def pid(self):
        return self._process.pid


class Worker:
    def __init__(
        self, ident: str, serve, server_settings, context: BaseContext
    ):
        self.ident = ident
        self.context = context
        self.serve = serve
        self.server_settings = server_settings
        self.processes: Set[WorkerProcess] = set()
        # self.health_queue: Queue[int] = Queue(maxsize=1)
        self.create_process()

    def create_process(self) -> WorkerProcess:
        process = WorkerProcess(
            factory=self.context.Process,
            name=f"Sanic-{self.ident}",
            target=self.serve,
            kwargs={
                **self.server_settings,
                # "health_queue": self.health_queue,
            },
        )
        self.processes.add(process)
        return process
