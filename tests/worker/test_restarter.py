from unittest.mock import Mock

import pytest

from sanic.worker.constants import ProcessState, RestartOrder
from sanic.worker.process import WorkerProcess
from sanic.worker.restarter import Restarter


def noop(*args, **kwargs):
    pass


def make_worker_process(
    name: str, state: ProcessState = ProcessState.STARTED
) -> WorkerProcess:
    worker_process = Mock()
    worker_process.restart = Mock()
    worker_process.name = name
    worker_process.state = state
    return worker_process


def test_restart_transient():
    transient = make_worker_process("Transient")
    durable = make_worker_process("Durable")
    restarter = Restarter()

    restarter.restart([transient], [durable])
    transient.restart.assert_called_once_with(
        restart_order=RestartOrder.SHUTDOWN_FIRST
    )
    durable.restart.assert_not_called()
    transient.restart.reset_mock()
    restarter.restart(
        [transient], [durable], restart_order=RestartOrder.STARTUP_FIRST
    )
    transient.restart.assert_called_once_with(
        restart_order=RestartOrder.STARTUP_FIRST
    )


@pytest.mark.parametrize(
    "state,called",
    (
        (ProcessState.IDLE, False),
        (ProcessState.RESTARTING, False),
        (ProcessState.STARTING, False),
        (ProcessState.STARTED, False),
        (ProcessState.ACKED, False),
        (ProcessState.JOINED, False),
        (ProcessState.TERMINATED, False),
        (ProcessState.FAILED, True),
        (ProcessState.COMPLETED, True),
        (ProcessState.NONE, True),
    ),
)
def test_restart_durable(caplog, state, called):
    transient = make_worker_process("Transient")
    durable = make_worker_process("Durable")
    restarter = Restarter()

    restarter.restart([transient], [durable], process_names=["Durable"])

    transient.restart.assert_not_called()
    durable.restart.assert_not_called()

    assert (
        "sanic.error",
        40,
        "Cannot restart process Durable because it is not in a "
        "final state. Current state is: STARTED.",
    ) in caplog.record_tuples
    assert (
        "sanic.error",
        40,
        "Failed to restart processes: Durable",
    ) in caplog.record_tuples

    durable.state = state
    restarter.restart([transient], [durable], process_names=["Durable"])

    transient.restart.assert_not_called()
    if called:
        durable.restart.assert_called_once_with(
            restart_order=RestartOrder.SHUTDOWN_FIRST
        )
    else:
        durable.restart.assert_not_called()
