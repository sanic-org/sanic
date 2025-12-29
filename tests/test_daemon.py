"""Tests for daemon mode functionality."""

import os
import signal
import sys

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from sanic.cli.app import SanicCLI
from sanic.compat import OS_IS_WINDOWS
from sanic.worker.daemon import (
    Daemon,
    DaemonError,
    PidfileInfo,
    _get_default_runtime_dir,
    _is_sanic_process,
    _process_exists,
    _sanitize_name,
)


pytestmark = pytest.mark.skipif(
    OS_IS_WINDOWS,
    reason="Daemon mode is not supported on Windows",
)


@pytest.fixture
def temp_pidfile(tmp_path):
    """Provide a temporary PID file path."""
    return tmp_path / "sanic.pid"


@pytest.fixture
def temp_logfile(tmp_path):
    """Provide a temporary log file path."""
    return tmp_path / "sanic.log"


@pytest.fixture
def temp_lockfile(tmp_path):
    """Provide a temporary lock file path."""
    return tmp_path / "sanic.lock"


# Helper Function Tests: _get_default_runtime_dir


def test_get_default_runtime_dir_uses_xdg(tmp_path):
    xdg_dir = tmp_path / "xdg_runtime"
    xdg_dir.mkdir()

    with patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(xdg_dir)}):
        result = _get_default_runtime_dir()

    assert result == xdg_dir / "sanic"
    assert result.exists()


def test_get_default_runtime_dir_falls_back_to_state_dir(tmp_path):
    mock_home = tmp_path / "home"
    mock_home.mkdir()

    with patch.dict(os.environ, {"XDG_RUNTIME_DIR": ""}, clear=False):
        with patch.object(Path, "home", return_value=mock_home):
            result = _get_default_runtime_dir()

    assert result == mock_home / ".local" / "state" / "sanic"
    assert result.exists()


def test_get_default_runtime_dir_xdg_mkdir_oserror(tmp_path):
    mock_home = tmp_path / "home"
    mock_home.mkdir()

    xdg_dir = tmp_path / "xdg_runtime"
    xdg_dir.mkdir()
    xdg_dir.chmod(0o444)

    try:
        with patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(xdg_dir)}):
            with patch.object(Path, "home", return_value=mock_home):
                result = _get_default_runtime_dir()
        assert "sanic" in str(result)
    finally:
        xdg_dir.chmod(0o755)


def test_get_default_runtime_dir_falls_back_to_cache_dir(tmp_path):
    mock_home = tmp_path / "home"
    mock_home.mkdir()
    cache_dir = mock_home / ".cache" / "sanic"

    call_count = {"count": 0}
    original_mkdir = Path.mkdir

    def selective_failing_mkdir(self, *args, **kwargs):
        call_count["count"] += 1
        # Fail for state_dir (first call after XDG fails), succeed for cache
        if ".local" in str(self) and "state" in str(self):
            raise OSError("Cannot create state directory")
        return original_mkdir(self, *args, **kwargs)

    with patch.dict(os.environ, {"XDG_RUNTIME_DIR": ""}, clear=False):
        with patch.object(Path, "home", return_value=mock_home):
            with patch.object(Path, "mkdir", selective_failing_mkdir):
                result = _get_default_runtime_dir()

    assert result == cache_dir


def test_get_default_runtime_dir_falls_back_to_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def failing_mkdir(self, *args, **kwargs):
        raise OSError("Cannot create directory")

    with patch.dict(os.environ, {"XDG_RUNTIME_DIR": ""}, clear=False):
        with patch.object(Path, "mkdir", failing_mkdir):
            result = _get_default_runtime_dir()

    assert result == Path.cwd()


# Helper Function Tests: _sanitize_name


def test_sanitize_name_alphanumeric():
    assert _sanitize_name("myapp") == "myapp"
    assert _sanitize_name("MyApp123") == "MyApp123"


def test_sanitize_name_allowed_special_chars():
    assert _sanitize_name("my-app") == "my-app"
    assert _sanitize_name("my_app") == "my_app"
    assert _sanitize_name("my.app") == "my.app"


def test_sanitize_name_replaces_invalid_chars():
    assert _sanitize_name("my app") == "my_app"
    assert _sanitize_name("my/app") == "my_app"
    assert _sanitize_name("my:app") == "my_app"


def test_sanitize_name_strips_dots_underscores():
    assert _sanitize_name("...myapp") == "myapp"
    assert _sanitize_name("myapp___") == "myapp"
    assert _sanitize_name("._myapp_.") == "myapp"


def test_sanitize_name_empty_returns_sanic():
    assert _sanitize_name("") == "sanic"
    assert _sanitize_name("...") == "sanic"
    assert _sanitize_name("___") == "sanic"


# Helper Function Tests: _process_exists


def test_process_exists_returns_true_for_current():
    assert _process_exists(os.getpid()) is True


def test_process_exists_returns_false_for_nonexistent():
    assert _process_exists(999999999) is False


def test_process_exists_returns_false_on_oserror():
    with patch("os.kill", side_effect=OSError("No such process")):
        assert _process_exists(12345) is False


# Helper Function Tests: _is_sanic_process


def test_is_sanic_process_returns_false_on_oserror():
    with patch("sanic.worker.daemon.Path") as mock_path:
        mock_cmdline = MagicMock()
        mock_cmdline.exists.return_value = True
        mock_cmdline.read_bytes.side_effect = OSError("Permission denied")
        mock_path.return_value = mock_cmdline

        result = _is_sanic_process(12345)
        assert result is False


def test_is_sanic_process_returns_true_when_proc_unavailable():
    with patch("sanic.worker.daemon.Path") as mock_path:
        mock_cmdline = MagicMock()
        mock_cmdline.exists.return_value = False
        mock_path.return_value = mock_cmdline

        result = _is_sanic_process(12345)
        assert result is True


def test_is_sanic_process_returns_true_when_sanic_found():
    with patch("sanic.worker.daemon.Path") as mock_path:
        mock_cmdline = MagicMock()
        mock_cmdline.exists.return_value = True
        mock_cmdline.read_bytes.return_value = b"python\x00-m\x00sanic\x00app"
        mock_path.return_value = mock_cmdline

        result = _is_sanic_process(12345)
        assert result is True


def test_is_sanic_process_returns_false_when_not_sanic():
    with patch("sanic.worker.daemon.Path") as mock_path:
        mock_cmdline = MagicMock()
        mock_cmdline.exists.return_value = True
        mock_cmdline.read_bytes.return_value = b"python\x00-m\x00flask\x00app"
        mock_path.return_value = mock_cmdline

        result = _is_sanic_process(12345)
        assert result is False


# PidfileInfo Tests


def test_pidfile_info_all_fields():
    info = PidfileInfo(pid=123, started=1234567890, name="testapp")
    assert info.pid == 123
    assert info.started == 1234567890
    assert info.name == "testapp"


def test_pidfile_info_defaults():
    info = PidfileInfo(pid=123)
    assert info.pid == 123
    assert info.started is None
    assert info.name is None


def test_pidfile_info_frozen():
    info = PidfileInfo(pid=123)
    with pytest.raises(Exception):
        info.pid = 456


# Daemon Initialization Tests


def test_daemon_init_with_explicit_pidfile(tmp_path):
    pidfile = tmp_path / "explicit.pid"
    daemon = Daemon(pidfile=str(pidfile))
    assert daemon.pidfile == pidfile


def test_daemon_init_with_auto_pidfile_and_name():
    daemon = Daemon(name="TestApp", pidfile="auto")
    assert daemon.pidfile is not None
    assert daemon.pidfile.name == "TestApp.pid"


def test_daemon_init_with_empty_pidfile_string():
    daemon = Daemon(name="TestApp", pidfile="")
    assert daemon.pidfile is not None
    assert daemon.pidfile.name == "TestApp.pid"


def test_daemon_init_with_auto_pidfile_no_name():
    daemon = Daemon(pidfile="auto")
    assert daemon.pidfile is not None
    # Should have a uuid-based name
    assert daemon.pidfile.name.startswith("sanic-")
    assert daemon.pidfile.name.endswith(".pid")


def test_daemon_init_with_explicit_lockfile(tmp_path):
    lockfile = tmp_path / "explicit.lock"
    daemon = Daemon(lockfile=str(lockfile))
    assert daemon._lockfile_path == lockfile


def test_daemon_init_no_pidfile():
    daemon = Daemon()
    assert daemon.pidfile is None


def test_daemon_init_with_logfile(tmp_path):
    logfile = tmp_path / "test.log"
    daemon = Daemon(logfile=str(logfile))
    assert daemon.logfile == logfile


def test_daemon_init_with_user_and_group():
    daemon = Daemon(user="testuser", group="testgroup")
    assert daemon.user == "testuser"
    assert daemon.group == "testgroup"


# Daemon Validation Tests


def test_validates_nonexistent_user(temp_pidfile):
    daemon = Daemon(pidfile=str(temp_pidfile), user="nonexistent_user_12345")

    with pytest.raises(DaemonError, match="does not exist"):
        daemon.validate()


def test_validates_nonexistent_group(temp_pidfile):
    daemon = Daemon(pidfile=str(temp_pidfile), group="nonexistent_group_12345")

    with pytest.raises(DaemonError, match="does not exist"):
        daemon.validate()


def test_validates_pidfile_directory():
    daemon = Daemon(pidfile="/nonexistent/path/sanic.pid")

    with pytest.raises(DaemonError, match="does not exist"):
        daemon.validate()


def test_validates_logfile_directory():
    daemon = Daemon(logfile="/nonexistent/path/sanic.log")

    with pytest.raises(DaemonError, match="does not exist"):
        daemon.validate()


def test_validates_lockfile_directory():
    daemon = Daemon(lockfile="/nonexistent/path/sanic.lock")

    with pytest.raises(DaemonError, match="does not exist"):
        daemon.validate()


def test_detects_already_running(temp_pidfile):
    temp_pidfile.write_text(f"sanic\npid={os.getpid()}\n")

    daemon = Daemon(pidfile=str(temp_pidfile))

    with patch("sanic.worker.daemon._is_sanic_process", return_value=True):
        with pytest.raises(DaemonError, match="already running"):
            daemon.validate()


def test_ignores_stale_pidfile(temp_pidfile):
    temp_pidfile.write_text("sanic\npid=999999999\n")

    daemon = Daemon(pidfile=str(temp_pidfile))
    daemon.validate()


def test_validates_without_pidfile(temp_logfile):
    daemon = Daemon(logfile=str(temp_logfile))
    daemon.validate()


def test_validate_writable_dir_not_writable(tmp_path):
    readonly_dir = tmp_path / "readonly"
    readonly_dir.mkdir()
    readonly_dir.chmod(0o444)

    try:
        daemon = Daemon(pidfile=str(readonly_dir / "test.pid"))
        with pytest.raises(DaemonError, match="Cannot write"):
            daemon.validate()
    finally:
        readonly_dir.chmod(0o755)


def test_validate_user_sets_uid_and_gid(temp_pidfile):
    daemon = Daemon(pidfile=str(temp_pidfile), user="root")
    daemon._validate_user_group()
    assert daemon._uid == 0
    assert daemon._gid is not None


def test_validate_group_sets_gid(temp_pidfile):
    daemon = Daemon(pidfile=str(temp_pidfile), group="root")
    daemon._validate_user_group()
    assert daemon._gid == 0


def test_validate_creates_default_lockfile(temp_pidfile):
    daemon = Daemon(pidfile=str(temp_pidfile))
    daemon._validate_paths()
    assert daemon._lockfile_path == temp_pidfile.with_suffix(".lock")


# PID File Tests


def test_writes_pidfile_with_marker(temp_pidfile):
    daemon = Daemon(pidfile=str(temp_pidfile))
    daemon._write_pidfile()

    assert temp_pidfile.exists()
    content = temp_pidfile.read_text()
    lines = content.strip().split("\n")
    assert lines[0] == "sanic"
    assert lines[1].startswith("pid=")
    pid = int(lines[1].split("=")[1])
    assert pid == os.getpid()


def test_writes_pidfile_with_name(temp_pidfile):
    daemon = Daemon(pidfile=str(temp_pidfile), name="MyApp")
    daemon._write_pidfile()

    content = temp_pidfile.read_text()
    assert "name=MyApp" in content


def test_writes_pidfile_with_started_timestamp(temp_pidfile):
    daemon = Daemon(pidfile=str(temp_pidfile))
    daemon._write_pidfile()

    content = temp_pidfile.read_text()
    assert "started=" in content


def test_write_pidfile_oserror(temp_pidfile):
    daemon = Daemon(pidfile=str(temp_pidfile))

    with patch.object(Path, "write_text", side_effect=OSError("Disk full")):
        with pytest.raises(DaemonError, match="Failed to write PID file"):
            daemon._write_pidfile()


def test_write_pidfile_skips_if_no_pidfile():
    daemon = Daemon()
    daemon._write_pidfile()  # Should not raise


def test_reads_pidfile_with_marker(temp_pidfile):
    temp_pidfile.write_text(f"sanic\npid={os.getpid()}\n")

    pid = Daemon.read_pidfile(temp_pidfile)
    assert pid == os.getpid()


def test_rejects_pidfile_without_marker(temp_pidfile):
    temp_pidfile.write_text(f"{os.getpid()}\n")

    pid = Daemon.read_pidfile(temp_pidfile)
    assert pid is None


def test_no_pidfile_when_not_requested():
    daemon = Daemon()
    assert daemon.pidfile is None


def test_name_pidfile_generation():
    daemon = Daemon(name="TestApp", pidfile="auto")
    assert daemon.pidfile is not None
    assert daemon.pidfile.name == "TestApp.pid"


def test_get_pidfile_path():
    path = Daemon.get_pidfile_path("MyApp")
    assert path.name == "MyApp.pid"


def test_removes_pidfile_on_cleanup(temp_pidfile):
    daemon = Daemon(pidfile=str(temp_pidfile))
    daemon._write_pidfile()

    assert temp_pidfile.exists()
    daemon._remove_pidfile()
    assert not temp_pidfile.exists()


def test_remove_pidfile_handles_missing_file(temp_pidfile):
    daemon = Daemon(pidfile=str(temp_pidfile))
    daemon._remove_pidfile()


def test_remove_pidfile_handles_oserror(temp_pidfile):
    daemon = Daemon(pidfile=str(temp_pidfile))
    temp_pidfile.write_text("test")

    with patch.object(
        Path, "unlink", side_effect=OSError("Permission denied")
    ):
        # Should not raise, just log
        daemon._remove_pidfile()


def test_remove_pidfile_skips_if_no_pidfile():
    daemon = Daemon()
    daemon._remove_pidfile()  # Should not raise


# read_pidfile_info Tests


def test_read_pidfile_info_returns_none_for_missing():
    result = Daemon.read_pidfile_info("/nonexistent/path.pid")
    assert result is None


def test_read_pidfile_info_returns_none_on_read_error(temp_pidfile):
    temp_pidfile.write_text("sanic\npid=123\n")

    with patch.object(Path, "read_text", side_effect=OSError("Read error")):
        result = Daemon.read_pidfile_info(temp_pidfile)
        assert result is None


def test_read_pidfile_info_returns_none_for_empty_file(temp_pidfile):
    temp_pidfile.write_text("")
    result = Daemon.read_pidfile_info(temp_pidfile)
    assert result is None


def test_read_pidfile_info_returns_none_without_sanic_marker(temp_pidfile):
    temp_pidfile.write_text("not_sanic\npid=123\n")
    result = Daemon.read_pidfile_info(temp_pidfile)
    assert result is None


def test_read_pidfile_info_returns_none_for_invalid_pid(temp_pidfile):
    temp_pidfile.write_text("sanic\npid=notanumber\n")
    result = Daemon.read_pidfile_info(temp_pidfile)
    assert result is None


def test_read_pidfile_info_returns_none_for_missing_pid(temp_pidfile):
    temp_pidfile.write_text("sanic\nstarted=123\n")
    result = Daemon.read_pidfile_info(temp_pidfile)
    assert result is None


def test_read_pidfile_info_handles_invalid_started(temp_pidfile):
    temp_pidfile.write_text("sanic\npid=123\nstarted=notanumber\n")
    result = Daemon.read_pidfile_info(temp_pidfile)
    assert result is not None
    assert result.pid == 123
    assert result.started is None


def test_read_pidfile_info_parses_all_fields(temp_pidfile):
    temp_pidfile.write_text(
        "sanic\npid=123\nstarted=1234567890\nname=testapp\n"
    )
    result = Daemon.read_pidfile_info(temp_pidfile)
    assert result is not None
    assert result.pid == 123
    assert result.started == 1234567890
    assert result.name == "testapp"


def test_read_pidfile_info_handles_empty_name(temp_pidfile):
    temp_pidfile.write_text("sanic\npid=123\nname=\n")
    result = Daemon.read_pidfile_info(temp_pidfile)
    assert result is not None
    assert result.name is None


# Lockfile Tests


def test_acquire_lockfile_success(temp_lockfile):
    daemon = Daemon(lockfile=str(temp_lockfile))
    daemon._acquire_lockfile()

    assert daemon._lock_fd is not None
    assert temp_lockfile.exists()

    # Cleanup
    daemon._release_lockfile()


def test_acquire_lockfile_skips_if_no_lockfile():
    daemon = Daemon()
    daemon._lockfile_path = None
    daemon._acquire_lockfile()  # Should not raise
    assert daemon._lock_fd is None


def test_acquire_lockfile_fails_when_locked(temp_lockfile):
    import fcntl

    # Acquire lock manually
    fd = os.open(str(temp_lockfile), os.O_RDWR | os.O_CREAT, 0o644)
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

    try:
        daemon = Daemon(lockfile=str(temp_lockfile))
        with pytest.raises(DaemonError, match="already running.*lock held"):
            daemon._acquire_lockfile()
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def test_acquire_lockfile_oserror_on_open(tmp_path):
    daemon = Daemon()
    daemon._lockfile_path = tmp_path / "nonexistent_dir" / "test.lock"

    with pytest.raises(DaemonError, match="Failed to open lock file"):
        daemon._acquire_lockfile()


def test_release_lockfile_skips_if_no_fd():
    daemon = Daemon()
    daemon._lock_fd = None
    daemon._release_lockfile()  # Should not raise


def test_release_lockfile_handles_unlock_oserror(temp_lockfile):
    import fcntl

    daemon = Daemon(lockfile=str(temp_lockfile))
    daemon._acquire_lockfile()

    with patch.object(fcntl, "flock", side_effect=OSError("Unlock failed")):
        # Should not raise, just log
        daemon._release_lockfile()


def test_release_lockfile_handles_close_oserror(temp_lockfile):
    daemon = Daemon(lockfile=str(temp_lockfile))
    daemon._acquire_lockfile()

    with patch("os.close", side_effect=OSError("Close failed")):
        # Should not raise, just log
        daemon._release_lockfile()


def test_release_lockfile_handles_unlink_oserror(temp_lockfile):
    daemon = Daemon(lockfile=str(temp_lockfile))
    daemon._acquire_lockfile()

    with patch.object(Path, "unlink", side_effect=OSError("Unlink failed")):
        # Should not raise, just log
        daemon._release_lockfile()


def test_release_lockfile_cleans_up(temp_lockfile):
    daemon = Daemon(lockfile=str(temp_lockfile))
    daemon._acquire_lockfile()

    assert daemon._lock_fd is not None
    daemon._release_lockfile()

    assert daemon._lock_fd is None


# Stream Redirection Tests


def test_redirect_streams_to_devnull(tmp_path, temp_pidfile):
    daemon = Daemon(pidfile=str(temp_pidfile))

    # Mock stdin/stdout/stderr fileno() and the os functions
    mock_stdin = MagicMock()
    mock_stdin.fileno.return_value = 0
    mock_stdin.flush = MagicMock()

    mock_stdout = MagicMock()
    mock_stdout.fileno.return_value = 1
    mock_stdout.flush = MagicMock()

    mock_stderr = MagicMock()
    mock_stderr.fileno.return_value = 2

    with patch("os.open") as mock_open:
        with patch("os.dup2"):
            with patch("os.close"):
                with patch.object(sys, "stdin", mock_stdin):
                    with patch.object(sys, "stdout", mock_stdout):
                        with patch.object(sys, "stderr", mock_stderr):
                            mock_open.return_value = 10
                            daemon._redirect_streams()

    # Should have opened /dev/null twice (for stdin and stdout/stderr)
    assert mock_open.call_count >= 2


def test_redirect_streams_to_logfile(temp_pidfile, temp_logfile):
    daemon = Daemon(pidfile=str(temp_pidfile), logfile=str(temp_logfile))

    mock_stdin = MagicMock()
    mock_stdin.fileno.return_value = 0
    mock_stdin.flush = MagicMock()

    mock_stdout = MagicMock()
    mock_stdout.fileno.return_value = 1
    mock_stdout.flush = MagicMock()

    mock_stderr = MagicMock()
    mock_stderr.fileno.return_value = 2

    with patch("os.open") as mock_open:
        with patch("os.dup2"):
            with patch("os.close"):
                with patch.object(sys, "stdin", mock_stdin):
                    with patch.object(sys, "stdout", mock_stdout):
                        with patch.object(sys, "stderr", mock_stderr):
                            mock_open.return_value = 10
                            daemon._redirect_streams()

    # Should have opened logfile
    calls = [str(c) for c in mock_open.call_args_list]
    assert any(str(temp_logfile) in c for c in calls)


# Signal Handler Tests


def test_setup_signal_handlers_skips_if_no_pidfile():
    daemon = Daemon()
    daemon._setup_signal_handlers()  # Should not raise


def test_setup_signal_handlers_installs_sighup(temp_pidfile):
    daemon = Daemon(pidfile=str(temp_pidfile))

    original_handler = signal.getsignal(signal.SIGHUP)
    try:
        daemon._setup_signal_handlers()

        # Check that a handler was installed
        new_handler = signal.getsignal(signal.SIGHUP)
        assert new_handler != original_handler
    finally:
        signal.signal(signal.SIGHUP, original_handler)


def test_sighup_handler_rewrites_pidfile(temp_pidfile):
    daemon = Daemon(pidfile=str(temp_pidfile))
    daemon._write_pidfile()

    original_handler = signal.getsignal(signal.SIGHUP)
    try:
        daemon._setup_signal_handlers()

        # Trigger SIGHUP
        handler = signal.getsignal(signal.SIGHUP)
        handler(signal.SIGHUP, None)

        # PID file should still exist with same pid
        assert temp_pidfile.exists()
        new_content = temp_pidfile.read_text()
        assert f"pid={os.getpid()}" in new_content
    finally:
        signal.signal(signal.SIGHUP, original_handler)


def test_sighup_handler_calls_original_handler(temp_pidfile):
    daemon = Daemon(pidfile=str(temp_pidfile))
    daemon._write_pidfile()

    handler_called = {"called": False, "signum": None}

    def custom_handler(signum, frame):
        handler_called["called"] = True
        handler_called["signum"] = signum

    original_handler = signal.getsignal(signal.SIGHUP)
    try:
        # Install a custom handler first
        signal.signal(signal.SIGHUP, custom_handler)

        # Now install daemon's handler which should chain to our custom one
        daemon._setup_signal_handlers()

        # Trigger SIGHUP
        handler = signal.getsignal(signal.SIGHUP)
        handler(signal.SIGHUP, None)

        # Both handlers should have run
        assert temp_pidfile.exists()
        assert handler_called["called"] is True
        assert handler_called["signum"] == signal.SIGHUP
    finally:
        signal.signal(signal.SIGHUP, original_handler)


# Daemon Process Tests


def test_daemonize_forks_twice(temp_pidfile, temp_logfile):
    fork_count = {"count": 0}

    def mock_fork():
        fork_count["count"] += 1
        return 0

    daemon = Daemon(pidfile=str(temp_pidfile), logfile=str(temp_logfile))

    with patch("os.fork", side_effect=mock_fork):
        with patch("os.setsid"):
            with patch("os.chdir"):
                with patch("os.umask"):
                    with patch.object(daemon, "_redirect_streams"):
                        with patch.object(daemon, "_write_pidfile"):
                            with patch.object(
                                daemon, "_setup_signal_handlers"
                            ):
                                daemon.validate = MagicMock()
                                daemon.daemonize()

    assert fork_count["count"] == 2


def test_daemonize_calls_validate(temp_pidfile):
    daemon = Daemon(pidfile=str(temp_pidfile))
    daemon.validate = MagicMock()

    with patch("os.fork", return_value=0):
        with patch("os.setsid"):
            with patch("os.chdir"):
                with patch("os.umask"):
                    with patch.object(daemon, "_redirect_streams"):
                        with patch.object(daemon, "_write_pidfile"):
                            with patch.object(
                                daemon, "_setup_signal_handlers"
                            ):
                                daemon.daemonize()

    daemon.validate.assert_called_once()


def test_daemonize_first_fork_error(temp_pidfile):
    daemon = Daemon(pidfile=str(temp_pidfile))
    daemon.validate = MagicMock()

    with patch("os.fork", side_effect=OSError("Fork failed")):
        with pytest.raises(DaemonError, match="First fork failed"):
            daemon.daemonize()


def test_daemonize_second_fork_error(temp_pidfile):
    daemon = Daemon(pidfile=str(temp_pidfile))
    daemon.validate = MagicMock()

    call_count = {"count": 0}

    def mock_fork():
        call_count["count"] += 1
        if call_count["count"] == 1:
            return 0
        raise OSError("Second fork failed")

    with patch("os.fork", side_effect=mock_fork):
        with patch("os.setsid"):
            with patch("os.chdir"):
                with patch("os.umask"):
                    with pytest.raises(
                        DaemonError, match="Second fork failed"
                    ):
                        daemon.daemonize()


def test_daemonize_acquires_lockfile(temp_pidfile, temp_lockfile):
    daemon = Daemon(pidfile=str(temp_pidfile), lockfile=str(temp_lockfile))
    daemon.validate = MagicMock()

    with patch("os.fork", return_value=0):
        with patch("os.setsid"):
            with patch("os.chdir"):
                with patch("os.umask"):
                    with patch.object(daemon, "_redirect_streams"):
                        with patch.object(daemon, "_write_pidfile"):
                            with patch.object(
                                daemon, "_setup_signal_handlers"
                            ):
                                with patch.object(
                                    daemon, "_acquire_lockfile"
                                ) as mock_acquire:
                                    daemon.daemonize()

    mock_acquire.assert_called_once()


# Privilege Tests


def test_drop_privileges_does_nothing_without_user_group():
    daemon = Daemon()
    daemon.drop_privileges()


def test_drop_privileges_warns_if_not_root(temp_pidfile):
    daemon = Daemon(pidfile=str(temp_pidfile), user="root")
    daemon._uid = 0
    daemon._gid = 0

    with patch("os.getuid", return_value=1000):  # Non-root
        # Should log warning but not raise
        daemon.drop_privileges()


def test_drop_privileges_requires_root(temp_pidfile):
    daemon = Daemon(pidfile=str(temp_pidfile), user="root")
    daemon._uid = 0
    daemon._gid = 0

    with patch("os.getuid", return_value=0):
        with patch("os.setgid", side_effect=PermissionError):
            with pytest.raises(DaemonError, match="Are you root"):
                daemon.drop_privileges()


def test_drop_privileges_setuid_error(temp_pidfile):
    daemon = Daemon(pidfile=str(temp_pidfile), user="root")
    daemon._uid = 0
    daemon._gid = None

    with patch("os.getuid", return_value=0):
        with patch("os.setuid", side_effect=PermissionError):
            with pytest.raises(DaemonError, match="Are you root"):
                daemon.drop_privileges()


def test_drop_privileges_sets_gid_and_initgroups(temp_pidfile):
    daemon = Daemon(pidfile=str(temp_pidfile), user="root", group="root")
    daemon._uid = 0
    daemon._gid = 0

    with patch("os.getuid", return_value=0):
        with patch("os.setgid") as mock_setgid:
            with patch("os.initgroups") as mock_initgroups:
                with patch("os.setuid") as mock_setuid:
                    daemon.drop_privileges()

    mock_setgid.assert_called_once_with(0)
    mock_initgroups.assert_called_once_with("root", 0)
    mock_setuid.assert_called_once_with(0)


def test_drop_privileges_skips_initgroups_without_user(temp_pidfile):
    daemon = Daemon(pidfile=str(temp_pidfile), group="root")
    daemon._uid = None
    daemon._gid = 0
    daemon.user = None

    with patch("os.getuid", return_value=0):
        with patch("os.setgid") as mock_setgid:
            with patch("os.initgroups") as mock_initgroups:
                daemon.drop_privileges()

    mock_setgid.assert_called_once_with(0)
    mock_initgroups.assert_not_called()


# Windows Check Tests


def test_raises_on_windows():
    with patch("sanic.worker.daemon.OS_IS_WINDOWS", True):
        from sanic.worker import daemon

        with patch.object(daemon, "OS_IS_WINDOWS", True):
            with pytest.raises(DaemonError, match="not supported on Windows"):
                daemon.Daemon()


# CLI Integration Tests


def test_daemon_flag_parsed():
    cli = SanicCLI()
    cli.attach()
    args = cli.parser.parse_args(
        ["fake.app:app", "--daemon", "--pidfile=/tmp/test.pid"]
    )

    assert args.daemon is True
    assert args.pidfile == "/tmp/test.pid"


def test_pidfile_without_daemon_fails():
    cli = SanicCLI()
    cli.attach()
    args = cli.parser.parse_args(["fake.app:app", "--pidfile=/tmp/test.pid"])

    with pytest.raises(SystemExit) as exc_info:
        for group in cli.groups:
            group.prepare(args)

    assert "require --daemon" in str(exc_info.value)


def test_logfile_without_daemon_fails():
    cli = SanicCLI()
    cli.attach()
    args = cli.parser.parse_args(["fake.app:app", "--logfile=/tmp/test.log"])

    with pytest.raises(SystemExit) as exc_info:
        for group in cli.groups:
            group.prepare(args)

    assert "require --daemon" in str(exc_info.value)


def test_daemon_with_dev_is_incompatible():
    cli = SanicCLI()
    cli.attach()
    args = cli.parser.parse_args(["fake.app:app", "--daemon", "--dev"])
    cli.args = args

    with pytest.raises(SystemExit):
        cli._setup_daemon("TestApp")


def test_daemon_with_auto_reload_is_incompatible():
    cli = SanicCLI()
    cli.attach()
    args = cli.parser.parse_args(["fake.app:app", "--daemon", "--auto-reload"])
    cli.args = args

    with pytest.raises(SystemExit):
        cli._setup_daemon("TestApp")


def test_daemon_with_repl_is_incompatible():
    cli = SanicCLI()
    cli.attach()
    args = cli.parser.parse_args(["fake.app:app", "--daemon", "--repl"])
    cli.args = args

    with pytest.raises(SystemExit):
        cli._setup_daemon("TestApp")


def test_user_group_options_parsed():
    cli = SanicCLI()
    cli.attach()
    args = cli.parser.parse_args(
        ["fake.app:app", "--daemon", "--user=nobody", "--group=nogroup"]
    )

    assert args.daemon_user == "nobody"
    assert args.daemon_group == "nogroup"


# Kill Command Tests (always SIGKILL)


def test_kill_command_parses_pid():
    with patch("sys.argv", ["sanic", "kill", "--pid", "12345"]):
        cli = SanicCLI()
        cli.attach()
        args = cli.parser.parse_args(["--pid", "12345"])

    assert args.pid == 12345
    assert args.pidfile is None


def test_kill_command_parses_pidfile():
    with patch(
        "sys.argv", ["sanic", "kill", "--pidfile", "/var/run/sanic.pid"]
    ):
        cli = SanicCLI()
        cli.attach()
        args = cli.parser.parse_args(["--pidfile", "/var/run/sanic.pid"])

    assert args.pidfile == "/var/run/sanic.pid"
    assert args.pid is None


def test_kill_command_requires_target():
    with patch("sys.argv", ["sanic", "kill"]):
        cli = SanicCLI()
        cli.attach()
        with pytest.raises(SystemExit):
            cli.parser.parse_args([])


def test_kill_always_sends_sigkill(temp_pidfile):
    pid = os.getpid()
    with open(temp_pidfile, "w") as f:
        f.write(f"sanic\npid={pid}\n")

    with patch("sys.argv", ["sanic", "kill", "--pidfile", str(temp_pidfile)]):
        cli = SanicCLI()
        cli.attach()
        with patch("os.kill") as mock_kill:
            cli._kill()
            mock_kill.assert_called_once_with(pid, signal.SIGKILL)


def test_kill_removes_pidfile_after_success(temp_pidfile):
    with open(temp_pidfile, "w") as f:
        f.write("sanic\npid=12345\n")

    with patch("sys.argv", ["sanic", "kill", "--pidfile", str(temp_pidfile)]):
        cli = SanicCLI()
        cli.attach()
        with patch("os.kill"):
            cli._kill()

    assert not temp_pidfile.exists()


def test_kill_handles_missing_pidfile(tmp_path):
    missing_pidfile = tmp_path / "nonexistent.pid"

    with patch(
        "sys.argv", ["sanic", "kill", "--pidfile", str(missing_pidfile)]
    ):
        cli = SanicCLI()
        cli.attach()
        with pytest.raises(SystemExit):
            cli._kill()


def test_kill_handles_process_not_found():
    with patch("sys.argv", ["sanic", "kill", "--pid", "999999999"]):
        cli = SanicCLI()
        cli.attach()
        with pytest.raises(SystemExit):
            cli._kill()


def test_kill_direct_pid():
    with patch("sys.argv", ["sanic", "kill", "--pid", "12345"]):
        cli = SanicCLI()
        cli.attach()
        with patch("os.kill") as mock_kill:
            cli._kill()
            mock_kill.assert_called_once_with(12345, signal.SIGKILL)


def test_kill_invalid_pidfile_fails(temp_pidfile):
    temp_pidfile.write_text("12345")

    with patch("sys.argv", ["sanic", "kill", "--pidfile", str(temp_pidfile)]):
        cli = SanicCLI()
        cli.attach()
        with pytest.raises(SystemExit):
            cli._kill()


# Status Command Tests


def test_status_command_parses_pid():
    with patch("sys.argv", ["sanic", "status", "--pid", "12345"]):
        cli = SanicCLI()
        cli.attach()
        args = cli.parser.parse_args(["--pid", "12345"])

    assert args.pid == 12345
    assert args.pidfile is None


def test_status_command_parses_pidfile():
    with patch(
        "sys.argv", ["sanic", "status", "--pidfile", "/var/run/sanic.pid"]
    ):
        cli = SanicCLI()
        cli.attach()
        args = cli.parser.parse_args(["--pidfile", "/var/run/sanic.pid"])

    assert args.pidfile == "/var/run/sanic.pid"
    assert args.pid is None


def test_status_command_requires_target():
    with patch("sys.argv", ["sanic", "status"]):
        cli = SanicCLI()
        cli.attach()
        with pytest.raises(SystemExit):
            cli.parser.parse_args([])


def test_status_running_process(temp_pidfile):
    pid = os.getpid()
    with open(temp_pidfile, "w") as f:
        f.write(f"sanic\npid={pid}\n")

    with patch(
        "sys.argv", ["sanic", "status", "--pidfile", str(temp_pidfile)]
    ):
        cli = SanicCLI()
        cli.attach()
        cli._status()


def test_status_not_running_process(temp_pidfile):
    with open(temp_pidfile, "w") as f:
        f.write("sanic\npid=999999999\n")

    with patch(
        "sys.argv", ["sanic", "status", "--pidfile", str(temp_pidfile)]
    ):
        cli = SanicCLI()
        cli.attach()
        with pytest.raises(SystemExit):
            cli._status()


def test_status_direct_pid_running():
    pid = os.getpid()

    with patch("sys.argv", ["sanic", "status", "--pid", str(pid)]):
        cli = SanicCLI()
        cli.attach()
        cli._status()


def test_status_direct_pid_not_running():
    with patch("sys.argv", ["sanic", "status", "--pid", "999999999"]):
        cli = SanicCLI()
        cli.attach()
        with pytest.raises(SystemExit):
            cli._status()


# Restart Command Tests (future use - not yet implemented)


def test_restart_command_parses_pid():
    with patch("sys.argv", ["sanic", "restart", "--pid", "12345"]):
        cli = SanicCLI()
        cli.attach()
        args = cli.parser.parse_args(["--pid", "12345"])

    assert args.pid == 12345
    assert args.pidfile is None


def test_restart_command_parses_pidfile():
    with patch(
        "sys.argv", ["sanic", "restart", "--pidfile", "/var/run/sanic.pid"]
    ):
        cli = SanicCLI()
        cli.attach()
        args = cli.parser.parse_args(["--pidfile", "/var/run/sanic.pid"])

    assert args.pidfile == "/var/run/sanic.pid"
    assert args.pid is None


def test_restart_command_requires_target():
    with patch("sys.argv", ["sanic", "restart"]):
        cli = SanicCLI()
        cli.attach()
        with pytest.raises(SystemExit):
            cli.parser.parse_args([])


def test_restart_not_implemented(temp_pidfile, capsys):
    pid = os.getpid()
    with open(temp_pidfile, "w") as f:
        f.write(f"sanic\npid={pid}\n")

    with patch(
        "sys.argv", ["sanic", "restart", "--pidfile", str(temp_pidfile)]
    ):
        cli = SanicCLI()
        cli.attach()
        with pytest.raises(SystemExit) as exc_info:
            cli._restart()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "not yet implemented" in captured.out
