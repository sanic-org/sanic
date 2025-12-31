from __future__ import annotations

import os
import signal
import sys

from argparse import ArgumentParser
from contextlib import suppress
from pathlib import Path

from sanic.worker.daemon import Daemon


def _add_target_args(parser: ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--pid",
        type=int,
        metavar="PID",
        help="Process ID of the daemon",
    )
    group.add_argument(
        "--pidfile",
        type=str,
        metavar="PATH",
        help="Path to PID file of the daemon",
    )


def make_kill_parser(parser: ArgumentParser) -> None:
    """Kill command always sends SIGKILL."""
    _add_target_args(parser)


def make_status_parser(parser: ArgumentParser) -> None:
    _add_target_args(parser)


def make_restart_parser(parser: ArgumentParser) -> None:
    _add_target_args(parser)


def resolve_target(
    pid: int | None, pidfile: str | None
) -> tuple[int, Path | None]:
    """
    Resolve a PID from either a direct PID or a pidfile path.

    Returns:
        Tuple of (pid, pidfile_path or None)

    Raises:
        SystemExit: If pidfile not found or invalid
    """
    if pid:
        return pid, None

    pidfile_path = Path(pidfile)  # type: ignore[arg-type]
    if not pidfile_path.exists():
        print(f"PID file not found: {pidfile_path}", file=sys.stderr)
        sys.exit(1)

    resolved_pid = Daemon.read_pidfile(pidfile_path)
    if resolved_pid is None:
        print(f"Invalid PID file: {pidfile_path}", file=sys.stderr)
        sys.exit(1)

    return resolved_pid, pidfile_path


def _terminate_process(
    pid: int, sig: signal.Signals, pidfile: Path | None = None
) -> None:
    """Send a signal to terminate a process and clean up pidfile."""
    sig_name = sig.name

    try:
        os.kill(pid, sig)
        print(f"Sent {sig_name} to process {pid}")
    except ProcessLookupError:
        print(f"Process {pid} not found", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(
            f"Permission denied to signal process {pid}. "
            "Are you running as the correct user?",
            file=sys.stderr,
        )
        sys.exit(1)
    except OSError as e:
        print(f"Failed to signal process {pid}: {e}", file=sys.stderr)
        sys.exit(1)

    if pidfile:
        if pidfile.exists():
            try:
                pidfile.unlink()
                print(f"Removed PID file: {pidfile}")
            except OSError as e:
                print(
                    f"Warning: Could not remove PID file {pidfile}: {e}",
                    file=sys.stderr,
                )
        lockfile = pidfile.with_suffix(".lock")
        if lockfile.exists():
            try:
                lockfile.unlink()
            except OSError:
                pass


def kill_daemon(pid: int, pidfile: Path | None = None) -> None:
    """Force kill a daemon process with SIGKILL."""
    _terminate_process(pid, signal.SIGKILL, pidfile)


def stop_daemon(
    pid: int, pidfile: Path | None = None, force: bool = False
) -> None:
    """Stop a daemon process gracefully (SIGTERM) or forcefully (SIGKILL)."""
    sig = signal.SIGKILL if force else signal.SIGTERM
    _terminate_process(pid, sig, pidfile)


def status_daemon(pid: int, pidfile: Path | None = None) -> bool:
    """
    Check if a daemon process is running.

    Args:
        pid: Process ID to check
        pidfile: Optional pidfile path to clean up if stale

    Returns:
        True if running, False otherwise (exits with code 1 if not)
    """
    try:
        os.kill(pid, 0)
        running = True
    except ProcessLookupError:
        running = False
    except PermissionError:
        running = True

    if running:
        print(f"Process {pid} is running")
        return True

    print(f"Process {pid} is NOT running")
    if pidfile and pidfile.exists():
        with suppress(OSError):
            pidfile.unlink()
            print(f"Removed stale PID file: {pidfile}")
    sys.exit(1)


def restart_daemon(pid: int) -> None:
    """
    Restart a daemon process.

    Args:
        pid: Process ID to restart (unused, for future use)
    """
    print("Restart is not yet implemented. Coming in a future release.")
    sys.exit(0)
