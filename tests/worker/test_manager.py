from logging import ERROR, INFO
from signal import SIGINT
from unittest.mock import Mock, call, patch

import pytest

from sanic.compat import OS_IS_WINDOWS
from sanic.exceptions import ServerKilled
from sanic.worker.constants import RestartOrder
from sanic.worker.manager import WorkerManager


if not OS_IS_WINDOWS:
    from signal import SIGKILL
else:
    SIGKILL = SIGINT


def fake_serve():
    ...


def test_manager_no_workers():
    message = "Cannot serve with no workers"
    with pytest.raises(RuntimeError, match=message):
        WorkerManager(0, fake_serve, {}, Mock(), (Mock(), Mock()), {})


@patch("sanic.worker.process.os")
def test_terminate(os_mock: Mock):
    process = Mock()
    process.pid = 1234
    context = Mock()
    context.Process.return_value = process
    manager = WorkerManager(1, fake_serve, {}, context, (Mock(), Mock()), {})
    manager.terminate()
    os_mock.kill.assert_called_once_with(1234, SIGINT)


@patch("sanic.worker.process.os")
def test_shutown(os_mock: Mock):
    process = Mock()
    process.pid = 1234
    process.is_alive.return_value = True
    context = Mock()
    context.Process.return_value = process
    manager = WorkerManager(1, fake_serve, {}, context, (Mock(), Mock()), {})
    manager.shutdown()
    os_mock.kill.assert_called_once_with(1234, SIGINT)


@patch("sanic.worker.manager.os")
def test_kill(os_mock: Mock):
    process = Mock()
    process.pid = 1234
    context = Mock()
    context.Process.return_value = process
    manager = WorkerManager(1, fake_serve, {}, context, (Mock(), Mock()), {})
    with pytest.raises(ServerKilled):
        manager.kill()
    os_mock.kill.assert_called_once_with(1234, SIGKILL)


@patch("sanic.worker.process.os")
@patch("sanic.worker.manager.os")
def test_shutdown_signal_send_kill(
    manager_os_mock: Mock, process_os_mock: Mock
):
    process = Mock()
    process.pid = 1234
    context = Mock()
    context.Process.return_value = process
    manager = WorkerManager(1, fake_serve, {}, context, (Mock(), Mock()), {})
    assert manager._shutting_down is False
    manager.shutdown_signal(SIGINT, None)
    assert manager._shutting_down is True
    process_os_mock.kill.assert_called_once_with(1234, SIGINT)
    manager.shutdown_signal(SIGINT, None)
    manager_os_mock.kill.assert_called_once_with(1234, SIGKILL)


def test_restart_all():
    p1 = Mock()
    p2 = Mock()
    context = Mock()
    context.Process.side_effect = [p1, p2, p1, p2]
    manager = WorkerManager(2, fake_serve, {}, context, (Mock(), Mock()), {})
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


@pytest.mark.parametrize("zero_downtime", (False, True))
def test_monitor_all(zero_downtime):
    p1 = Mock()
    p2 = Mock()
    sub = Mock()
    incoming = (
        "__ALL_PROCESSES__::STARTUP_FIRST"
        if zero_downtime
        else "__ALL_PROCESSES__:"
    )
    sub.recv.side_effect = [incoming, ""]
    context = Mock()
    context.Process.side_effect = [p1, p2]
    manager = WorkerManager(2, fake_serve, {}, context, (Mock(), sub), {})
    manager.restart = Mock()  # type: ignore
    manager.wait_for_ack = Mock()  # type: ignore
    manager.monitor()

    restart_order = (
        RestartOrder.STARTUP_FIRST
        if zero_downtime
        else RestartOrder.SHUTDOWN_FIRST
    )
    manager.restart.assert_called_once_with(
        process_names=None,
        reloaded_files="",
        restart_order=restart_order,
    )


@pytest.mark.parametrize("zero_downtime", (False, True))
def test_monitor_all_with_files(zero_downtime):
    p1 = Mock()
    p2 = Mock()
    sub = Mock()
    incoming = (
        "__ALL_PROCESSES__:foo,bar:STARTUP_FIRST"
        if zero_downtime
        else "__ALL_PROCESSES__:foo,bar"
    )
    sub.recv.side_effect = [incoming, ""]
    context = Mock()
    context.Process.side_effect = [p1, p2]
    manager = WorkerManager(2, fake_serve, {}, context, (Mock(), sub), {})
    manager.restart = Mock()  # type: ignore
    manager.wait_for_ack = Mock()  # type: ignore
    manager.monitor()

    restart_order = (
        RestartOrder.STARTUP_FIRST
        if zero_downtime
        else RestartOrder.SHUTDOWN_FIRST
    )
    manager.restart.assert_called_once_with(
        process_names=None,
        reloaded_files="foo,bar",
        restart_order=restart_order,
    )


@pytest.mark.parametrize("zero_downtime", (False, True))
def test_monitor_one_process(zero_downtime):
    p1 = Mock()
    p1.name = "Testing"
    p2 = Mock()
    sub = Mock()
    incoming = (
        f"{p1.name}:foo,bar:STARTUP_FIRST"
        if zero_downtime
        else f"{p1.name}:foo,bar"
    )
    sub.recv.side_effect = [incoming, ""]
    context = Mock()
    context.Process.side_effect = [p1, p2]
    manager = WorkerManager(2, fake_serve, {}, context, (Mock(), sub), {})
    manager.restart = Mock()  # type: ignore
    manager.wait_for_ack = Mock()  # type: ignore
    manager.monitor()

    restart_order = (
        RestartOrder.STARTUP_FIRST
        if zero_downtime
        else RestartOrder.SHUTDOWN_FIRST
    )
    manager.restart.assert_called_once_with(
        process_names=[p1.name],
        reloaded_files="foo,bar",
        restart_order=restart_order,
    )


def test_shutdown_signal():
    pub = Mock()
    manager = WorkerManager(1, fake_serve, {}, Mock(), (pub, Mock()), {})
    manager.shutdown = Mock()  # type: ignore

    manager.shutdown_signal(SIGINT, None)
    pub.send.assert_called_with(None)
    manager.shutdown.assert_called_once_with()


def test_shutdown_servers(caplog):
    p1 = Mock()
    p1.pid = 1234
    context = Mock()
    context.Process.side_effect = [p1]
    pub = Mock()
    manager = WorkerManager(1, fake_serve, {}, context, (pub, Mock()), {})

    with patch("os.kill") as kill:
        with caplog.at_level(ERROR):
            manager.shutdown_server()

            kill.assert_called_once_with(1234, SIGINT)
            kill.reset_mock()

            assert not caplog.record_tuples

            manager.shutdown_server()

            kill.assert_not_called()

            assert (
                "sanic.error",
                ERROR,
                "Server shutdown failed because a server was not found.",
            ) in caplog.record_tuples


def test_shutdown_servers_named():
    p1 = Mock()
    p1.pid = 1234
    p2 = Mock()
    p2.pid = 6543
    context = Mock()
    context.Process.side_effect = [p1, p2]
    pub = Mock()
    manager = WorkerManager(2, fake_serve, {}, context, (pub, Mock()), {})

    with patch("os.kill") as kill:
        with pytest.raises(KeyError):
            manager.shutdown_server("foo")
        manager.shutdown_server("Server-1")

        kill.assert_called_once_with(6543, SIGINT)


def test_scale(caplog):
    p1 = Mock()
    p1.pid = 1234
    p2 = Mock()
    p2.pid = 3456
    p3 = Mock()
    p3.pid = 5678
    context = Mock()
    context.Process.side_effect = [p1, p2, p3]
    pub = Mock()
    manager = WorkerManager(1, fake_serve, {}, context, (pub, Mock()), {})

    assert len(manager.transient) == 1

    manager.scale(3)
    assert len(manager.transient) == 3

    with patch("os.kill") as kill:
        manager.scale(2)
        assert len(manager.transient) == 2

        manager.scale(1)
        assert len(manager.transient) == 1

        kill.call_count == 2

    with caplog.at_level(INFO):
        manager.scale(1)

    assert (
        "sanic.root",
        INFO,
        "No change needed. There are already 1 workers.",
    ) in caplog.record_tuples

    with pytest.raises(ValueError, match=r"Cannot scale to 0 workers\."):
        manager.scale(0)
