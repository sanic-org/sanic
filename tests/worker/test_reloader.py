import signal

from asyncio import Event
from pathlib import Path
from unittest.mock import Mock

import pytest

from sanic.app import Sanic
from sanic.worker.loader import AppLoader
from sanic.worker.reloader import Reloader


@pytest.fixture
def reloader():
    ...


@pytest.fixture
def app():
    app = Sanic("Test")

    @app.route("/")
    def handler(_):
        ...

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

    def check_file(filename, mtimes):
        return not after.is_set()

    @app.before_reload_trigger
    async def before_reload_trigger(_):
        before.set()

    @app.after_reload_trigger
    async def after_reload_trigger(_):
        after.set()

    reloader = Reloader(Mock(), 0.1, set(), app_loader)
    reloader.check_file = check_file  # type: ignore
    run_reloader(reloader)

    assert before.is_set()
    assert after.is_set()


def test_check_file(tmp_path):
    current = tmp_path / "testing.txt"
    current.touch()
    mtimes = {}
    assert Reloader.check_file(current, mtimes) is False
    assert len(mtimes) == 1
    assert Reloader.check_file(current, mtimes) is False
    mtimes[current] = mtimes[current] - 1
    assert Reloader.check_file(current, mtimes) is True
