from __future__ import annotations

from asyncio import sleep
from dataclasses import dataclass
from datetime import datetime, timedelta
from multiprocessing import Manager
from queue import Empty, Full
from signal import SIGINT, SIGTERM
from signal import signal as signal_func
from typing import TYPE_CHECKING, Optional

from sanic.application.constants import ServerStage
from sanic.log import logger


if TYPE_CHECKING:
    from sanic import Sanic


class Stale(ValueError):
    ...


@dataclass
class HealthState:
    name: str
    last: Optional[datetime] = None
    misses: int = 0

    def report(self, timestamp: int) -> None:
        logger.debug(f"Reporting {self.name}")
        self.last = datetime.fromtimestamp(timestamp)
        self.misses = 0

    def missed(self) -> None:
        self.misses += 1
        logger.info(
            f"Missed health check for {self.name} "
            f"({self.misses}/{HealthMonitor.MAX_MISSES})"
        )
        if self.misses >= HealthMonitor.MAX_MISSES:
            raise Stale

    def check(self) -> None:
        if not self.last:
            return

        if self.last < (
            datetime.now()
            - (
                timedelta(seconds=HealthMonitor.MISSED_THRESHHOLD)
                * (self.misses + 1)
            )
        ):
            self.missed()

    def reset(self) -> None:
        self.misses = 0
        self.last = datetime.now()


def send_healthy(name, queue):
    health = (name, datetime.now().timestamp())
    logger.debug(f"Sending health: {health}", extra={"verbosity": 2})
    try:
        queue.put_nowait(health)
    except Full:
        ...


async def health_check(app: Sanic):
    sent = datetime.now()

    while app.state.stage is ServerStage.SERVING:
        now = datetime.now()
        if sent < now - timedelta(seconds=HealthMonitor.REPORT_INTERVAL):
            send_healthy(app.m.name, app.shared_ctx.health_queue)
            sent = now
        await sleep(0.1)


async def start_health_check(app: Sanic):
    app.add_task(health_check(app))


async def prepare_health_monitor(app, *_):
    HealthMonitor.prepare(app)


async def setup_health_monitor(app, *_):
    health = HealthMonitor(app)
    process_names = [
        process.name for process in app.manager.transient_processes
    ]
    app.manager.manage(
        "HealthMonitor",
        health,
        {
            "process_names": process_names,
            "health_queue": app.shared_ctx.health_queue,
        },
    )


class HealthMonitor:
    MAX_MISSES = 3
    REPORT_INTERVAL = 2
    MISSED_THRESHHOLD = 5

    def __init__(self, app: Sanic):
        self.run = True
        self.restart_publisher = app.manager.restart_publisher

    def __call__(self, process_names, health_queue) -> None:
        signal_func(SIGINT, self.stop)
        signal_func(SIGTERM, self.stop)

        now = datetime.now()
        health_state = {
            process_name: HealthState(last=now, name=process_name)
            for process_name in process_names
        }
        while self.run:
            try:
                name, timestamp = health_queue.get_nowait()
            except Empty:
                ...
            else:
                health_state[name].report(timestamp)

            for state in health_state.values():
                try:
                    state.check()
                except Stale:
                    state.reset()
                    self.restart_publisher.send(state.name)

    def stop(self, *_):
        self.run = False

    @classmethod
    def prepare(cls, app: Sanic):
        sync_manager = Manager()
        health_queue = sync_manager.Queue(maxsize=app.state.workers * 2)
        app.shared_ctx.health_queue = health_queue

    @classmethod
    def setup(
        cls,
        app: Sanic,
        max_misses: int = 3,
        report_interval: int = 5,
        missed_threshhold: int = 7,
    ):
        HealthMonitor.MAX_MISSES = max_misses
        HealthMonitor.REPORT_INTERVAL = report_interval
        HealthMonitor.MISSED_THRESHHOLD = missed_threshhold
        app.main_process_start(prepare_health_monitor)
        app.main_process_ready(setup_health_monitor)
        app.after_server_start(start_health_check)
