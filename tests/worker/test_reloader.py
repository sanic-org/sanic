import os
import re
import signal
import sys
import threading

from asyncio import Event
from logging import DEBUG
from multiprocessing import get_context
from multiprocessing.connection import wait
from pathlib import Path
from time import sleep
from unittest.mock import Mock

import pytest

from sanic.app import Sanic
from sanic.worker.constants import ProcessState, RestartOrder
from sanic.worker.loader import AppLoader
from sanic.worker.process import WorkerProcess
from sanic.worker.reloader import Reloader


@pytest.fixture
def reloader(): ...


@pytest.fixture
def app():
    app = Sanic("Test")

    @app.route("/")
    def handler(_): ...

    return app


@pytest.fixture
def app_loader(app):
    return AppLoader(factory=lambda: app)


def run_reloader(reloader):
    def stop(*_):
        reloader.stop()

    signal.signal(signal.SIGALRM, stop)
    signal.alarm(1)
    reloader()


def is_python_file(filename):
    return (isinstance(filename, Path) and (filename.suffix == "py")) or (
        isinstance(filename, str) and filename.endswith(".py")
    )


def ignore_termination(ready, release):
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    ready.set()
    release.wait()


def finish_on_termination(ready, stopping, release):
    signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGTERM})
    ready.send(None)
    signal.sigwait({signal.SIGTERM})
    stopping.send(None)
    release.recv()


@pytest.fixture
def restarting_processes(monkeypatch):
    context = get_context("spawn")
    children = []
    threads = []

    def factory(**kwargs):
        child = context.Process(**kwargs)
        children.append(child)
        return child

    def thread_factory(**kwargs):
        thread = threading.Thread(**kwargs)
        threads.append(thread)
        return thread

    monkeypatch.setattr("sanic.worker.process.Thread", thread_factory)
    yield context, factory, children, threads
    for child in children:
        if child.pid is not None:
            child.kill()
            child.join(timeout=5)
    for thread in threads:
        thread.join(timeout=5)


def test_reload_send():
    publisher = Mock()
    reloader = Reloader(publisher, 0.1, set(), Mock())
    reloader.reload("foobar")
    publisher.send.assert_called_once_with("__ALL_PROCESSES__:foobar")


def test_iter_files():
    reloader = Reloader(Mock(), 0.1, set(), Mock())
    len_python_files = len(list(reloader.files()))
    assert len_python_files > 0

    static_dir = Path(__file__).parent.parent / "static"
    len_static_files = len(list(static_dir.glob("**/*")))
    reloader = Reloader(Mock(), 0.1, set({static_dir}), Mock())
    len_total_files = len(list(reloader.files()))
    assert len_static_files > 0
    assert len_total_files == len_python_files + len_static_files


@pytest.mark.parametrize(
    "order,expected",
    (
        (
            RestartOrder.SHUTDOWN_FIRST,
            [
                "Restarting a process",
                "Begin restart termination",
                "Starting a process",
            ],
        ),
        (
            RestartOrder.STARTUP_FIRST,
            [
                "Restarting a process",
                "Starting a process",
                "Begin restart termination",
                "Waiting for process to be acked",
                "Process acked. Terminating",
            ],
        ),
    ),
)
def test_default_reload_shutdown_order(monkeypatch, caplog, order, expected):
    current_process = Mock()

    def mark_terminated():
        current_process.is_alive.return_value = False

    current_process.terminate.side_effect = mark_terminated
    worker_process = WorkerProcess(
        lambda **_: current_process,
        "Test",
        "TST",
        lambda **_: ...,
        {},
        {},
    )

    def start(self):
        worker_process.set_state(ProcessState.ACKED)
        self._target(*self._args, **self._kwargs)

    orig = threading.Thread.start
    monkeypatch.setattr(threading.Thread, "start", start)

    with caplog.at_level(DEBUG):
        worker_process.restart(restart_order=order)

    ansi = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    def clean(msg: str):
        msg, _ = ansi.sub("", msg).split(":", 1)
        return msg

    debug = [clean(record[2]) for record in caplog.record_tuples]
    assert debug == expected
    current_process.start.assert_called_once()
    current_process.terminate.assert_called_once()
    monkeypatch.setattr(threading.Thread, "start", orig)


def test_reload_delayed(monkeypatch):
    monkeypatch.setattr(WorkerProcess, "THRESHOLD", 1)

    current_process = Mock()
    worker_process = WorkerProcess(
        lambda **_: current_process,
        "Test",
        "TST",
        lambda **_: ...,
        {},
        {},
    )

    def start(self):
        sleep(0.2)
        self._target(*self._args, **self._kwargs)

    orig = threading.Thread.start
    monkeypatch.setattr(threading.Thread, "start", start)

    message = "Worker Test failed to come ack within 0.1 seconds"
    with pytest.raises(TimeoutError, match=message):
        worker_process.restart(restart_order=RestartOrder.STARTUP_FIRST)

    monkeypatch.setattr(threading.Thread, "start", orig)


@pytest.mark.skipif(sys.platform == "win32", reason="Requires waitpid")
def test_startup_first_restart_reaps_old_process(monkeypatch):
    context = get_context("spawn")
    shutdown = context.Event()
    children = []
    threads = []

    def factory(**kwargs):
        child = context.Process(**kwargs)
        children.append(child)
        return child

    worker = WorkerProcess(factory, "Test", "TST", shutdown.wait, {}, {})

    def thread_factory(**kwargs):
        thread = threading.Thread(**kwargs)
        threads.append(thread)
        return thread

    monkeypatch.setattr("sanic.worker.process.Thread", thread_factory)
    try:
        worker.start()
        old_process = children[0]

        worker.restart(restart_order=RestartOrder.STARTUP_FIRST)
        worker.set_state(ProcessState.ACKED)
        threads[0].join(timeout=5)

        assert not threads[0].is_alive()
        assert wait([old_process.sentinel], timeout=5)
        # Unlike Process.is_alive(), waitpid does not silently reap a zombie
        # before we can check whether the restart already collected it.
        with pytest.raises(ChildProcessError):
            os.waitpid(old_process.pid, os.WNOHANG)
        assert worker.is_alive()
    finally:
        worker.set_state(ProcessState.ACKED, force=True)
        for child in children:
            if child.pid is not None:
                child.kill()
                child.join(timeout=5)
        for thread in threads:
            thread.join(timeout=5)


@pytest.mark.skipif(sys.platform == "win32", reason="Requires waitpid")
@pytest.mark.parametrize("first, second", ((0, 1), (1, 0)))
def test_overlapping_startup_first_restarts_reap_each_old_process(
    monkeypatch, first, second
):
    context = get_context("spawn")
    shutdown = context.Event()
    children = []
    threads = []

    def factory(**kwargs):
        child = context.Process(**kwargs)
        children.append(child)
        return child

    def thread_factory(**kwargs):
        thread = threading.Thread(**kwargs)
        # Delay execution until both restarts have scheduled their cleanup.
        monkeypatch.setattr(thread, "start", lambda: None)
        threads.append(thread)
        return thread

    worker = WorkerProcess(factory, "Test", "TST", shutdown.wait, {}, {})
    monkeypatch.setattr("sanic.worker.process.Thread", thread_factory)
    try:
        worker.start()
        worker.restart(restart_order=RestartOrder.STARTUP_FIRST)
        worker.restart(restart_order=RestartOrder.STARTUP_FIRST)
        worker.set_state(ProcessState.ACKED)

        threads[first].run()
        threads[second].run()

        with pytest.raises(ChildProcessError):
            os.waitpid(children[0].pid, os.WNOHANG)
        with pytest.raises(ChildProcessError):
            os.waitpid(children[1].pid, os.WNOHANG)
        assert worker.is_alive()
    finally:
        for child in children:
            if child.pid is not None:
                child.kill()
                child.join(timeout=5)


@pytest.mark.skipif(sys.platform == "win32", reason="Requires POSIX signals")
def test_startup_first_kills_worker_that_ignores_termination(
    monkeypatch, restarting_processes
):
    context, factory, children, threads = restarting_processes
    ready = context.Event()
    release = context.Event()
    monkeypatch.setattr(WorkerProcess, "SHUTDOWN_TIMEOUT", 0.1, raising=False)
    worker = WorkerProcess(
        factory,
        "Test",
        "TST",
        ignore_termination,
        {"ready": ready, "release": release},
        {},
    )
    worker.start()
    assert ready.wait(timeout=5)

    worker.restart(restart_order=RestartOrder.STARTUP_FIRST)
    worker.set_state(ProcessState.ACKED)
    threads[0].join(timeout=5)

    assert not threads[0].is_alive()
    with pytest.raises(ChildProcessError):
        os.waitpid(children[0].pid, os.WNOHANG)
    assert children[0].exitcode == -signal.SIGKILL
    assert worker.is_alive()


@pytest.mark.skipif(sys.platform == "win32", reason="Requires POSIX signals")
def test_startup_first_allows_graceful_exit_before_shutdown_timeout(
    restarting_processes,
):
    context, factory, children, threads = restarting_processes
    ready, notify_ready = context.Pipe(duplex=False)
    stopping, notify_stopping = context.Pipe(duplex=False)
    proceed, release = context.Pipe(duplex=False)
    with ready, notify_ready, stopping, notify_stopping, proceed, release:
        worker = WorkerProcess(
            factory,
            "Test",
            "TST",
            finish_on_termination,
            {
                "ready": notify_ready,
                "stopping": notify_stopping,
                "release": proceed,
            },
            {},
        )
        worker.start()
        assert ready.poll(timeout=5)

        worker.restart(restart_order=RestartOrder.STARTUP_FIRST)
        worker.set_state(ProcessState.ACKED)
        assert stopping.poll(timeout=5)
        assert threads[0].is_alive()
        release.send(None)
        threads[0].join(timeout=5)

        assert not threads[0].is_alive()
        with pytest.raises(ChildProcessError):
            os.waitpid(children[0].pid, os.WNOHANG)
        assert children[0].exitcode == 0
        assert worker.is_alive()


def test_startup_first_reports_worker_that_survives_kill(monkeypatch):
    child = Mock()
    child.is_alive.return_value = True
    worker = WorkerProcess(
        lambda **_: child,
        "Test",
        "TST",
        lambda: None,
        {},
        {},
    )
    worker.start()

    def run_cleanup(thread):
        worker.set_state(ProcessState.ACKED)
        thread.run()

    monkeypatch.setattr(threading.Thread, "start", run_cleanup)
    with pytest.raises(
        TimeoutError, match="failed to exit after being killed"
    ):
        worker.restart(restart_order=RestartOrder.STARTUP_FIRST)


def test_reloader_triggers_start_stop_listeners(
    app: Sanic, app_loader: AppLoader
):
    results = []

    @app.reload_process_start
    def reload_process_start(_):
        results.append("reload_process_start")

    @app.reload_process_stop
    def reload_process_stop(_):
        results.append("reload_process_stop")

    reloader = Reloader(Mock(), 0.1, set(), app_loader)
    run_reloader(reloader)

    assert results == ["reload_process_start", "reload_process_stop"]


def test_not_triggered(app_loader):
    reload_dir = Path(__file__).parent.parent / "fake"
    publisher = Mock()
    reloader = Reloader(publisher, 0.1, {reload_dir}, app_loader)
    run_reloader(reloader)

    publisher.send.assert_not_called()


def test_triggered(app_loader):
    paths = set()

    def check_file(filename, mtimes):
        if (isinstance(filename, Path) and (filename.name == "server.py")) or (
            isinstance(filename, str) and "sanic/app.py" in filename
        ):
            paths.add(str(filename))
            return True
        return False

    reload_dir = Path(__file__).parent.parent / "fake"
    publisher = Mock()
    reloader = Reloader(publisher, 0.1, {reload_dir}, app_loader)
    reloader.check_file = check_file  # type: ignore
    run_reloader(reloader)

    assert len(paths) == 2

    publisher.send.assert_called()
    call_arg = publisher.send.call_args_list[0][0][0]
    assert call_arg.startswith("__ALL_PROCESSES__:")
    assert call_arg.count(",") == 1
    for path in paths:
        assert str(path) in call_arg


def test_reloader_triggers_reload_listeners(app: Sanic, app_loader: AppLoader):
    before = Event()
    after = Event()
    changed_files = set()

    def check_file(filename, mtimes):
        return not after.is_set()

    @app.before_reload_trigger
    async def before_reload_trigger(_):
        before.set()

    @app.after_reload_trigger
    async def after_reload_trigger(_, changed):
        after.set()
        changed_files.update(changed)

    reloader = Reloader(Mock(), 0.1, set(), app_loader)
    reloader.check_file = check_file  # type: ignore
    run_reloader(reloader)

    assert before.is_set()
    assert after.is_set()
    assert len(changed_files) > 0
    assert changed_files == set(reloader.files())


def test_check_file(tmp_path):
    current = tmp_path / "testing.txt"
    current.touch()
    mtimes = {}
    assert Reloader.check_file(current, mtimes) is False
    assert len(mtimes) == 1
    assert Reloader.check_file(current, mtimes) is False
    mtimes[current] = mtimes[current] - 1
    assert Reloader.check_file(current, mtimes) is True
