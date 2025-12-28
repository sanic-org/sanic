"""Tests for daemon mode functionality."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from sanic.compat import OS_IS_WINDOWS


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


# Daemon Validation Tests


def test_validates_nonexistent_user(temp_pidfile):
    from sanic.worker.daemon import Daemon, DaemonError

    daemon = Daemon(pidfile=str(temp_pidfile), user="nonexistent_user_12345")

    with pytest.raises(DaemonError, match="does not exist"):
        daemon.validate()


def test_validates_nonexistent_group(temp_pidfile):
    from sanic.worker.daemon import Daemon, DaemonError

    daemon = Daemon(pidfile=str(temp_pidfile), group="nonexistent_group_12345")

    with pytest.raises(DaemonError, match="does not exist"):
        daemon.validate()


def test_validates_pidfile_directory():
    from sanic.worker.daemon import Daemon, DaemonError

    daemon = Daemon(pidfile="/nonexistent/path/sanic.pid")

    with pytest.raises(DaemonError, match="does not exist"):
        daemon.validate()


def test_validates_logfile_directory():
    from sanic.worker.daemon import Daemon, DaemonError

    daemon = Daemon(logfile="/nonexistent/path/sanic.log")

    with pytest.raises(DaemonError, match="does not exist"):
        daemon.validate()


def test_detects_already_running(temp_pidfile):
    from sanic.worker.daemon import Daemon, DaemonError

    temp_pidfile.write_text(f"sanic\npid={os.getpid()}\n")

    daemon = Daemon(pidfile=str(temp_pidfile))

    with patch("sanic.worker.daemon._is_sanic_process", return_value=True):
        with pytest.raises(DaemonError, match="already running"):
            daemon.validate()


def test_ignores_stale_pidfile(temp_pidfile):
    from sanic.worker.daemon import Daemon

    temp_pidfile.write_text("sanic\npid=999999999\n")

    daemon = Daemon(pidfile=str(temp_pidfile))
    daemon.validate()


def test_validates_without_pidfile(temp_logfile):
    from sanic.worker.daemon import Daemon

    daemon = Daemon(logfile=str(temp_logfile))
    daemon.validate()


# PID File Tests


def test_writes_pidfile_with_marker(temp_pidfile):
    from sanic.worker.daemon import Daemon

    daemon = Daemon(pidfile=str(temp_pidfile))
    daemon._write_pidfile()

    assert temp_pidfile.exists()
    content = temp_pidfile.read_text()
    lines = content.strip().split("\n")
    assert lines[0] == "sanic"
    assert lines[1].startswith("pid=")
    pid = int(lines[1].split("=")[1])
    assert pid == os.getpid()


def test_reads_pidfile_with_marker(temp_pidfile):
    from sanic.worker.daemon import Daemon

    temp_pidfile.write_text(f"sanic\npid={os.getpid()}\n")

    pid = Daemon.read_pidfile(temp_pidfile)
    assert pid == os.getpid()


def test_rejects_pidfile_without_marker(temp_pidfile):
    from sanic.worker.daemon import Daemon

    temp_pidfile.write_text(f"{os.getpid()}\n")

    pid = Daemon.read_pidfile(temp_pidfile)
    assert pid is None


def test_no_pidfile_when_not_requested():
    from sanic.worker.daemon import Daemon

    daemon = Daemon()
    assert daemon.pidfile is None


def test_name_pidfile_generation():
    from sanic.worker.daemon import Daemon

    daemon = Daemon(name="TestApp", pidfile="auto")
    assert daemon.pidfile is not None
    assert daemon.pidfile.name == "TestApp.pid"


def test_get_pidfile_path():
    from sanic.worker.daemon import Daemon

    path = Daemon.get_pidfile_path("MyApp")
    assert path.name == "MyApp.pid"


def test_removes_pidfile_on_cleanup(temp_pidfile):
    from sanic.worker.daemon import Daemon

    daemon = Daemon(pidfile=str(temp_pidfile))
    daemon._write_pidfile()

    assert temp_pidfile.exists()
    daemon._remove_pidfile()
    assert not temp_pidfile.exists()


def test_remove_pidfile_handles_missing_file(temp_pidfile):
    from sanic.worker.daemon import Daemon

    daemon = Daemon(pidfile=str(temp_pidfile))
    daemon._remove_pidfile()


# Daemon Process Tests


def test_daemonize_forks_twice(temp_pidfile, temp_logfile):
    from sanic.worker.daemon import Daemon

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
                            with patch.object(daemon, "_setup_signal_handlers"):
                                daemon.validate = MagicMock()
                                daemon.daemonize()

    assert fork_count["count"] == 2


def test_daemonize_calls_validate(temp_pidfile):
    from sanic.worker.daemon import Daemon

    daemon = Daemon(pidfile=str(temp_pidfile))
    daemon.validate = MagicMock()

    with patch("os.fork", return_value=0):
        with patch("os.setsid"):
            with patch("os.chdir"):
                with patch("os.umask"):
                    with patch.object(daemon, "_redirect_streams"):
                        with patch.object(daemon, "_write_pidfile"):
                            with patch.object(daemon, "_setup_signal_handlers"):
                                daemon.daemonize()

    daemon.validate.assert_called_once()


# Privilege Tests


def test_drop_privileges_does_nothing_without_user_group():
    from sanic.worker.daemon import Daemon

    daemon = Daemon()
    daemon.drop_privileges()


def test_drop_privileges_requires_root(temp_pidfile):
    from sanic.worker.daemon import Daemon, DaemonError

    daemon = Daemon(pidfile=str(temp_pidfile), user="root")
    daemon._uid = 0
    daemon._gid = 0

    with patch("os.getuid", return_value=0):
        with patch("os.setgid", side_effect=PermissionError):
            with pytest.raises(DaemonError, match="Are you running as root"):
                daemon.drop_privileges()


# Windows Check Tests


def test_raises_on_windows():
    from sanic.worker.daemon import DaemonError

    with patch("sanic.worker.daemon.OS_IS_WINDOWS", True):
        from sanic.worker import daemon

        with patch.object(daemon, "OS_IS_WINDOWS", True):
            with pytest.raises(DaemonError, match="not supported on Windows"):
                daemon.Daemon()


# CLI Integration Tests


def test_daemon_flag_parsed():
    from sanic.cli.app import SanicCLI

    cli = SanicCLI()
    cli.attach()
    args = cli.parser.parse_args(
        ["fake.app:app", "--daemon", "--pidfile=/tmp/test.pid"]
    )

    assert args.daemon is True
    assert args.pidfile == "/tmp/test.pid"


def test_pidfile_without_daemon_fails():
    from sanic.cli.app import SanicCLI

    cli = SanicCLI()
    cli.attach()
    args = cli.parser.parse_args(["fake.app:app", "--pidfile=/tmp/test.pid"])

    with pytest.raises(SystemExit) as exc_info:
        for group in cli.groups:
            group.prepare(args)

    assert "require --daemon" in str(exc_info.value)


def test_logfile_without_daemon_fails():
    from sanic.cli.app import SanicCLI

    cli = SanicCLI()
    cli.attach()
    args = cli.parser.parse_args(["fake.app:app", "--logfile=/tmp/test.log"])

    with pytest.raises(SystemExit) as exc_info:
        for group in cli.groups:
            group.prepare(args)

    assert "require --daemon" in str(exc_info.value)


def test_daemon_with_dev_is_incompatible():
    from sanic.cli.app import SanicCLI

    cli = SanicCLI()
    cli.attach()
    args = cli.parser.parse_args(["fake.app:app", "--daemon", "--dev"])
    cli.args = args

    with pytest.raises(SystemExit):
        cli._setup_daemon("TestApp")


def test_daemon_with_auto_reload_is_incompatible():
    from sanic.cli.app import SanicCLI

    cli = SanicCLI()
    cli.attach()
    args = cli.parser.parse_args(["fake.app:app", "--daemon", "--auto-reload"])
    cli.args = args

    with pytest.raises(SystemExit):
        cli._setup_daemon("TestApp")


def test_daemon_with_repl_is_incompatible():
    from sanic.cli.app import SanicCLI

    cli = SanicCLI()
    cli.attach()
    args = cli.parser.parse_args(["fake.app:app", "--daemon", "--repl"])
    cli.args = args

    with pytest.raises(SystemExit):
        cli._setup_daemon("TestApp")


def test_user_group_options_parsed():
    from sanic.cli.app import SanicCLI

    cli = SanicCLI()
    cli.attach()
    args = cli.parser.parse_args(
        ["fake.app:app", "--daemon", "--user=nobody", "--group=nogroup"]
    )

    assert args.daemon_user == "nobody"
    assert args.daemon_group == "nogroup"


# Kill Command Tests (always SIGKILL)


def test_kill_command_parses_pid():
    from sanic.cli.app import SanicCLI

    with patch("sys.argv", ["sanic", "kill", "--pid", "12345"]):
        cli = SanicCLI()
        cli.attach()
        args = cli.parser.parse_args(["--pid", "12345"])

    assert args.pid == 12345
    assert args.pidfile is None


def test_kill_command_parses_pidfile():
    from sanic.cli.app import SanicCLI

    with patch("sys.argv", ["sanic", "kill", "--pidfile", "/var/run/sanic.pid"]):
        cli = SanicCLI()
        cli.attach()
        args = cli.parser.parse_args(["--pidfile", "/var/run/sanic.pid"])

    assert args.pidfile == "/var/run/sanic.pid"
    assert args.pid is None


def test_kill_command_requires_target():
    from sanic.cli.app import SanicCLI

    with patch("sys.argv", ["sanic", "kill"]):
        cli = SanicCLI()
        cli.attach()
        with pytest.raises(SystemExit):
            cli.parser.parse_args([])


def test_kill_always_sends_sigkill(temp_pidfile):
    import signal

    from sanic.cli.app import SanicCLI

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
    from sanic.cli.app import SanicCLI

    with open(temp_pidfile, "w") as f:
        f.write("sanic\npid=12345\n")

    with patch("sys.argv", ["sanic", "kill", "--pidfile", str(temp_pidfile)]):
        cli = SanicCLI()
        cli.attach()
        with patch("os.kill"):
            cli._kill()

    assert not temp_pidfile.exists()


def test_kill_handles_missing_pidfile(tmp_path):
    from sanic.cli.app import SanicCLI

    missing_pidfile = tmp_path / "nonexistent.pid"

    with patch("sys.argv", ["sanic", "kill", "--pidfile", str(missing_pidfile)]):
        cli = SanicCLI()
        cli.attach()
        with pytest.raises(SystemExit):
            cli._kill()


def test_kill_handles_process_not_found():
    from sanic.cli.app import SanicCLI

    with patch("sys.argv", ["sanic", "kill", "--pid", "999999999"]):
        cli = SanicCLI()
        cli.attach()
        with pytest.raises(SystemExit):
            cli._kill()


def test_kill_direct_pid():
    import signal

    from sanic.cli.app import SanicCLI

    with patch("sys.argv", ["sanic", "kill", "--pid", "12345"]):
        cli = SanicCLI()
        cli.attach()
        with patch("os.kill") as mock_kill:
            cli._kill()
            mock_kill.assert_called_once_with(12345, signal.SIGKILL)


def test_kill_invalid_pidfile_fails(temp_pidfile):
    from sanic.cli.app import SanicCLI

    temp_pidfile.write_text("12345")

    with patch("sys.argv", ["sanic", "kill", "--pidfile", str(temp_pidfile)]):
        cli = SanicCLI()
        cli.attach()
        with pytest.raises(SystemExit):
            cli._kill()


# Status Command Tests


def test_status_command_parses_pid():
    from sanic.cli.app import SanicCLI

    with patch("sys.argv", ["sanic", "status", "--pid", "12345"]):
        cli = SanicCLI()
        cli.attach()
        args = cli.parser.parse_args(["--pid", "12345"])

    assert args.pid == 12345
    assert args.pidfile is None


def test_status_command_parses_pidfile():
    from sanic.cli.app import SanicCLI

    with patch("sys.argv", ["sanic", "status", "--pidfile", "/var/run/sanic.pid"]):
        cli = SanicCLI()
        cli.attach()
        args = cli.parser.parse_args(["--pidfile", "/var/run/sanic.pid"])

    assert args.pidfile == "/var/run/sanic.pid"
    assert args.pid is None


def test_status_command_requires_target():
    from sanic.cli.app import SanicCLI

    with patch("sys.argv", ["sanic", "status"]):
        cli = SanicCLI()
        cli.attach()
        with pytest.raises(SystemExit):
            cli.parser.parse_args([])


def test_status_running_process(temp_pidfile):
    from sanic.cli.app import SanicCLI

    pid = os.getpid()
    with open(temp_pidfile, "w") as f:
        f.write(f"sanic\npid={pid}\n")

    with patch("sys.argv", ["sanic", "status", "--pidfile", str(temp_pidfile)]):
        cli = SanicCLI()
        cli.attach()
        cli._status()


def test_status_not_running_process(temp_pidfile):
    from sanic.cli.app import SanicCLI

    with open(temp_pidfile, "w") as f:
        f.write("sanic\npid=999999999\n")

    with patch("sys.argv", ["sanic", "status", "--pidfile", str(temp_pidfile)]):
        cli = SanicCLI()
        cli.attach()
        with pytest.raises(SystemExit):
            cli._status()


def test_status_direct_pid_running():
    from sanic.cli.app import SanicCLI

    pid = os.getpid()

    with patch("sys.argv", ["sanic", "status", "--pid", str(pid)]):
        cli = SanicCLI()
        cli.attach()
        cli._status()


def test_status_direct_pid_not_running():
    from sanic.cli.app import SanicCLI

    with patch("sys.argv", ["sanic", "status", "--pid", "999999999"]):
        cli = SanicCLI()
        cli.attach()
        with pytest.raises(SystemExit):
            cli._status()


# Restart Command Tests (future use - not yet implemented)


def test_restart_command_parses_pid():
    from sanic.cli.app import SanicCLI

    with patch("sys.argv", ["sanic", "restart", "--pid", "12345"]):
        cli = SanicCLI()
        cli.attach()
        args = cli.parser.parse_args(["--pid", "12345"])

    assert args.pid == 12345
    assert args.pidfile is None


def test_restart_command_parses_pidfile():
    from sanic.cli.app import SanicCLI

    with patch("sys.argv", ["sanic", "restart", "--pidfile", "/var/run/sanic.pid"]):
        cli = SanicCLI()
        cli.attach()
        args = cli.parser.parse_args(["--pidfile", "/var/run/sanic.pid"])

    assert args.pidfile == "/var/run/sanic.pid"
    assert args.pid is None


def test_restart_command_requires_target():
    from sanic.cli.app import SanicCLI

    with patch("sys.argv", ["sanic", "restart"]):
        cli = SanicCLI()
        cli.attach()
        with pytest.raises(SystemExit):
            cli.parser.parse_args([])


def test_restart_not_implemented(temp_pidfile, capsys):
    from sanic.cli.app import SanicCLI

    pid = os.getpid()
    with open(temp_pidfile, "w") as f:
        f.write(f"sanic\npid={pid}\n")

    with patch("sys.argv", ["sanic", "restart", "--pidfile", str(temp_pidfile)]):
        cli = SanicCLI()
        cli.attach()
        with pytest.raises(SystemExit) as exc_info:
            cli._restart()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "not yet implemented" in captured.out
