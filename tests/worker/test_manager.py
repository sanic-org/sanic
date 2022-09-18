from signal import SIGINT, SIGKILL
from unittest.mock import Mock, call, patch

import pytest

from sanic.worker.manager import WorkerManager


def fake_serve():
    ...


def test_manager_no_workers():
    message = "Cannot serve with no workers"
    with pytest.raises(RuntimeError, match=message):
        WorkerManager(
            0,
            fake_serve,
            {},
            Mock(),
            (Mock(), Mock()),
            {},
        )


@patch("sanic.worker.process.os")
def test_terminate(os_mock: Mock):
    process = Mock()
    process.pid = 1234
    context = Mock()
    context.Process.return_value = process
    manager = WorkerManager(
        1,
        fake_serve,
        {},
        context,
        (Mock(), Mock()),
        {},
    )
    assert manager.terminated is False
    manager.terminate()
    assert manager.terminated is True
    os_mock.kill.assert_called_once_with(1234, SIGINT)


@patch("sanic.worker.process.os")
def test_shutown(os_mock: Mock):
    process = Mock()
    process.pid = 1234
    process.is_alive.return_value = True
    context = Mock()
    context.Process.return_value = process
    manager = WorkerManager(
        1,
        fake_serve,
        {},
        context,
        (Mock(), Mock()),
        {},
    )
    manager.shutdown()
    os_mock.kill.assert_called_once_with(1234, SIGINT)


@patch("sanic.worker.manager.os")
def test_kill(os_mock: Mock):
    process = Mock()
    process.pid = 1234
    context = Mock()
    context.Process.return_value = process
    manager = WorkerManager(
        1,
        fake_serve,
        {},
        context,
        (Mock(), Mock()),
        {},
    )
    manager.kill()
    os_mock.kill.assert_called_once_with(1234, SIGKILL)


def test_restart_all():
    p1 = Mock()
    p2 = Mock()
    context = Mock()
    context.Process.side_effect = [p1, p2, p1, p2]
    manager = WorkerManager(
        2,
        fake_serve,
        {},
        context,
        (Mock(), Mock()),
        {},
    )
    assert len(list(manager.transient_processes))
    manager.restart()
    p1.terminate.assert_called_once()
    p2.terminate.assert_called_once()
    context.Process.assert_has_calls(
        [
            call(
                name="Sanic-Server-0-0",
                target=fake_serve,
                kwargs={"config": {}},
                daemon=True,
            ),
            call(
                name="Sanic-Server-1-0",
                target=fake_serve,
                kwargs={"config": {}},
                daemon=True,
            ),
            call(
                name="Sanic-Server-0-0",
                target=fake_serve,
                kwargs={"config": {}},
                daemon=True,
            ),
            call(
                name="Sanic-Server-1-0",
                target=fake_serve,
                kwargs={"config": {}},
                daemon=True,
            ),
        ]
    )


def test_monitor_all():
    p1 = Mock()
    p2 = Mock()
    sub = Mock()
    sub.recv.side_effect = ["__ALL_PROCESSES__:", ""]
    context = Mock()
    context.Process.side_effect = [p1, p2]
    manager = WorkerManager(
        2,
        fake_serve,
        {},
        context,
        (Mock(), sub),
        {},
    )
    manager.restart = Mock()  # type: ignore
    manager.wait_for_ack = Mock()  # type: ignore
    manager.monitor()

    manager.restart.assert_called_once_with(
        process_names=None, reloaded_files=""
    )


def test_monitor_all_with_files():
    p1 = Mock()
    p2 = Mock()
    sub = Mock()
    sub.recv.side_effect = ["__ALL_PROCESSES__:foo,bar", ""]
    context = Mock()
    context.Process.side_effect = [p1, p2]
    manager = WorkerManager(
        2,
        fake_serve,
        {},
        context,
        (Mock(), sub),
        {},
    )
    manager.restart = Mock()  # type: ignore
    manager.wait_for_ack = Mock()  # type: ignore
    manager.monitor()

    manager.restart.assert_called_once_with(
        process_names=None, reloaded_files="foo,bar"
    )


def test_monitor_one_process():
    p1 = Mock()
    p1.name = "Testing"
    p2 = Mock()
    sub = Mock()
    sub.recv.side_effect = [f"{p1.name}:foo,bar", ""]
    context = Mock()
    context.Process.side_effect = [p1, p2]
    manager = WorkerManager(
        2,
        fake_serve,
        {},
        context,
        (Mock(), sub),
        {},
    )
    manager.restart = Mock()  # type: ignore
    manager.wait_for_ack = Mock()  # type: ignore
    manager.monitor()

    manager.restart.assert_called_once_with(
        process_names=[p1.name], reloaded_files="foo,bar"
    )


def test_shutdown_signal():
    pub = Mock()
    manager = WorkerManager(
        1,
        fake_serve,
        {},
        Mock(),
        (pub, Mock()),
        {},
    )
    manager.shutdown = Mock()  # type: ignore

    manager.shutdown_signal(SIGINT, None)
    pub.send.assert_called_with(None)
    manager.shutdown.assert_called_once_with()
