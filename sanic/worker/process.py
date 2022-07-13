from enum import IntEnum, auto

# from multiprocessing import Queue
from typing import Set

from sanic.log import logger


class ProcessState(IntEnum):
    IDLE = auto()
    STARTED = auto()
    JOINED = auto()
    TERMINATED = auto()


class WorkerProcess:
    def __init__(self, process):
        self.state = ProcessState.IDLE
        self.misses = 0
        self._process = process

    def set_state(self, state: ProcessState, force=False):
        if not force and state < self.state:
            raise Exception("...")
        self.state = state

    def start(self):
        logger.debug("Starting a process")
        self.set_state(ProcessState.STARTED)
        self._process.start()

    def join(self):
        self.set_state(ProcessState.JOINED)
        self._process.join()

    def terminate(self):
        logger.debug(f"Terminating {self.pid}")
        self.set_state(ProcessState.TERMINATED, force=True)
        self._process.terminate()

    def is_alive(self):
        return self._process.is_alive()

    def missed(self):
        self.misses += 1

    @property
    def pid(self):
        return self._process.pid


class Worker:
    def __init__(self, ident: int, serve, server_settings, context):
        self.ident = ident
        self.context = context
        self.serve = serve
        self.server_settings = server_settings
        self.processes: Set[WorkerProcess] = set()
        # self.health_queue: Queue[int] = Queue(maxsize=1)
        self.create_process()

    def create_process(self) -> WorkerProcess:
        subprocess = self.context.Process(
            target=self.serve,
            kwargs={
                **self.server_settings,
                # "health_queue": self.health_queue,
            },
        )
        subprocess.daemon = True
        process = WorkerProcess(subprocess)
        self.processes.add(process)
        return process
