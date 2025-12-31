from __future__ import annotations

import atexit
import grp
import os
import pwd
import signal
import sys
import time
import uuid

from dataclasses import dataclass
from pathlib import Path

from sanic.compat import OS_IS_WINDOWS
from sanic.log import logger


try:
    import fcntl  # type: ignore
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    fcntl = None  # type: ignore


def _get_default_runtime_dir() -> Path:
    """
    Default directory for auto-generated runtime artifacts (pid/lock/log).

    Priority:
      1) XDG_RUNTIME_DIR/sanic  (preferred, runtime-only)
      2) ~/.local/state/sanic   (persistent state, modern default)
      3) ~/.cache/sanic         (fallback)
      4) cwd                    (last resort)
    """
    xdg_runtime = os.environ.get("XDG_RUNTIME_DIR")
    if xdg_runtime:
        path = Path(xdg_runtime) / "sanic"
        try:
            path.mkdir(mode=0o700, parents=True, exist_ok=True)
            return path
        except OSError:
            pass

    state_dir = Path.home() / ".local" / "state" / "sanic"
    try:
        state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        return state_dir
    except OSError:
        pass

    cache_dir = Path.home() / ".cache" / "sanic"
    try:
        cache_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        return cache_dir
    except OSError:
        pass

    return Path.cwd()


def _sanitize_name(name: str) -> str:
    return (
        "".join(
            c if c.isalnum() or c in ("-", "_", ".") else "_" for c in name
        ).strip("._")
        or "sanic"
    )


def _process_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _is_sanic_process(pid: int) -> bool:
    """
    Best-effort Sanic process identification.

    On Linux, checks /proc/<pid>/cmdline for 'sanic'. On other platforms,
    falls back to True if process exists (no strong identification).
    """
    proc_cmdline = Path(f"/proc/{pid}/cmdline")
    if proc_cmdline.exists():
        try:
            data = proc_cmdline.read_bytes()
            return b"sanic" in data
        except OSError:
            return False
    return True


@dataclass(frozen=True)
class PidfileInfo:
    pid: int
    started: int | None = None
    name: str | None = None


class DaemonError(Exception):
    pass


class Daemon:
    """
    Daemonization helper (Unix only).

    Supports:
      - Double-fork daemonization
      - Optional PID file (with Sanic marker + metadata)
      - Optional lock file (prevents double start / stale PID reuse issues)
      - Optional logfile redirection
      - Optional privilege drop (user/group)
      - SIGHUP handler that preserves pidfile identity
    """

    def __init__(
        self,
        pidfile: str | None = None,
        logfile: str | None = None,
        user: str | None = None,
        group: str | None = None,
        name: str | None = None,
        lockfile: str | None = None,
    ):
        if OS_IS_WINDOWS:
            raise DaemonError(
                "Daemon mode is not supported on Windows. "
                "Consider using a Windows service or nssm instead."
            )

        self.name = _sanitize_name(name) if name else None

        self._auto_pidfile = pidfile == "auto" or pidfile == ""
        self.pidfile: Path | None
        if self._auto_pidfile:
            base = _get_default_runtime_dir()
            # Prefer deterministic name if provided
            if self.name:
                self.pidfile = base / f"{self.name}.pid"
            else:
                self.pidfile = base / f"sanic-{uuid.uuid4().hex}.pid"
        elif pidfile:
            self.pidfile = Path(pidfile)
        else:
            self.pidfile = None

        self.logfile = Path(logfile) if logfile else None
        self.user = user
        self.group = group

        self._uid: int | None = None
        self._gid: int | None = None
        self.pid: int | None = None

        self._lockfile_path: Path | None = Path(lockfile) if lockfile else None
        self._lock_fd: int | None = None

    @staticmethod
    def get_pidfile_path(name: str) -> Path:
        """
        Get the predictable pidfile path for a given name.

        Args:
            name: The application/daemon name

        Returns:
            Path to the pidfile in the default runtime directory
        """
        sanitized = _sanitize_name(name)
        return _get_default_runtime_dir() / f"{sanitized}.pid"

    def validate(self) -> None:
        self._validate_user_group()
        self._validate_paths()
        self._validate_runtime_state()

    def daemonize(self) -> None:
        """
        Double-fork daemonization.

        Important: anything meant for the invoking terminal must be
        printed/logged before calling this method, since stdout/stderr
        are redirected after detaching.
        """
        self.validate()

        # Acquire lock before forking to prevent race condition
        # The lock is inherited by child processes and remains held
        self._acquire_lockfile()

        # First fork
        try:
            pid = os.fork()
            if pid > 0:
                os._exit(0)  # pragma: no cover
        except OSError as e:
            raise DaemonError(f"First fork failed: {e}") from e

        os.chdir("/")
        os.setsid()
        os.umask(0o022)

        # Second fork
        try:
            pid = os.fork()
            if pid > 0:
                os._exit(0)  # pragma: no cover
        except OSError as e:
            raise DaemonError(f"Second fork failed: {e}") from e

        self.pid = os.getpid()

        self._redirect_streams()
        self._write_pidfile()
        self._setup_signal_handlers()

        logger.info(
            "Sanic daemon started",
            extra={
                "daemon_pid": self.pid,
                "daemon_pidfile": str(self.pidfile) if self.pidfile else None,
                "daemon_logfile": str(self.logfile) if self.logfile else None,
                "daemon_name": self.name,
            },
        )

    def drop_privileges(self) -> None:
        """
        Drop privileges to configured user/group.

        Call after binding privileged ports but before serving requests.
        """
        if self._uid is None and self._gid is None:
            return

        if os.getuid() != 0:
            logger.warning(
                "Privilege drop requested but not running as root",
                extra={"user": self.user, "group": self.group},
            )
            return

        if self._gid is not None:
            try:
                os.setgid(self._gid)
                if self.user:
                    os.initgroups(self.user, self._gid)
            except PermissionError as e:
                grp = self.group or self._gid
                raise DaemonError(
                    f"Cannot change group to '{grp}'. Are you root?"
                ) from e

        if self._uid is not None:
            try:
                os.setuid(self._uid)
            except PermissionError as e:
                usr = self.user or self._uid
                raise DaemonError(
                    f"Cannot change user to '{usr}'. Are you root?"
                ) from e

        logger.info(
            "Dropped privileges",
            extra={
                "user": self.user or "unchanged",
                "group": self.group or "unchanged",
            },
        )

    def _validate_user_group(self) -> None:
        if not self.user and not self.group:
            return

        if self.user:
            try:
                pw = pwd.getpwnam(self.user)
            except KeyError as e:
                raise DaemonError(f"User '{self.user}' does not exist") from e
            self._uid = pw.pw_uid
            if not self.group:
                self._gid = pw.pw_gid

        if self.group:
            try:
                gr = grp.getgrnam(self.group)
            except KeyError as e:
                raise DaemonError(
                    f"Group '{self.group}' does not exist"
                ) from e
            self._gid = gr.gr_gid

    def _validate_paths(self) -> None:
        if self.pidfile:
            self._validate_writable_dir(self.pidfile, "PID file")

        if self.logfile:
            self._validate_writable_dir(self.logfile, "Log file")

        # Default lockfile beside pidfile if not explicitly set
        if not self._lockfile_path and self.pidfile:
            self._lockfile_path = self.pidfile.with_suffix(".lock")

        if self._lockfile_path:
            self._validate_writable_dir(self._lockfile_path, "Lock file")

    def _validate_runtime_state(self) -> None:
        # PID file check (stale vs running)
        if not self.pidfile or not self.pidfile.exists():
            return

        info = self.read_pidfile_info(self.pidfile)
        if not info:
            return

        if _process_exists(info.pid) and _is_sanic_process(info.pid):
            raise DaemonError(f"Daemon already running with PID {info.pid}")

    def _validate_writable_dir(self, path: Path, label: str) -> None:
        directory = path.parent
        if not directory.exists():
            raise DaemonError(f"{label} directory does not exist: {directory}")
        if not os.access(directory, os.W_OK):
            raise DaemonError(
                f"Cannot write to {label} directory: {directory}"
            )

    def _write_pidfile(self) -> None:
        if not self.pidfile:
            return

        pid = os.getpid()
        started = int(time.time())
        name = self.name or ""

        # Format:
        #   sanic
        #   pid=123
        #   started=...
        #   name=...
        lines = [
            "sanic",
            f"pid={pid}",
            f"started={started}",
        ]
        if name:
            lines.append(f"name={name}")

        try:
            self.pidfile.write_text("\n".join(lines) + "\n")
        except OSError as e:
            raise DaemonError(
                f"Failed to write PID file: {self.pidfile}"
            ) from e

        atexit.register(self._remove_pidfile)

    def _remove_pidfile(self) -> None:
        if not self.pidfile:
            return
        try:
            self.pidfile.unlink(missing_ok=True)
        except OSError as e:
            # Best-effort cleanup: failure to remove the PID file is non-fatal.
            logger.debug("Failed to remove PID file %s: %s", self.pidfile, e)

    @staticmethod
    def read_pidfile(pidfile: str | Path) -> int | None:
        info = Daemon.read_pidfile_info(pidfile)
        return info.pid if info else None

    @staticmethod
    def read_pidfile_info(pidfile: str | Path) -> PidfileInfo | None:
        path = Path(pidfile)
        if not path.exists():
            return None

        try:
            raw = path.read_text().splitlines()
        except OSError:
            return None

        if not raw or raw[0].strip() != "sanic":
            return None

        data: dict[str, str] = {}
        for line in raw[1:]:
            if "=" in line:
                k, v = line.split("=", 1)
                data[k.strip()] = v.strip()

        try:
            pid = int(data.get("pid", ""))
        except ValueError:
            return None

        started = None
        if "started" in data:
            try:
                started = int(data["started"])
            except ValueError:
                started = None

        name = data.get("name") or None
        return PidfileInfo(pid=pid, started=started, name=name)

    def _acquire_lockfile(self) -> None:
        if not self._lockfile_path:
            return
        if fcntl is None:
            return

        try:
            fd = os.open(
                str(self._lockfile_path), os.O_RDWR | os.O_CREAT, 0o644
            )
        except OSError as e:
            raise DaemonError(
                f"Failed to open lock file: {self._lockfile_path}"
            ) from e

        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as e:
            try:
                os.close(fd)
            except OSError:
                pass
            raise DaemonError(
                f"Daemon already running (lock held): {self._lockfile_path}"
            ) from e

        self._lock_fd = fd
        atexit.register(self._release_lockfile)

    def _release_lockfile(self) -> None:
        if self._lock_fd is None:
            return
        try:
            if fcntl is not None:
                fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
        except OSError as e:
            # Best-effort cleanup: failure to unlock is non-fatal.
            logger.debug(
                "Failed to unlock file descriptor %s: %s", self._lock_fd, e
            )
        try:
            os.close(self._lock_fd)
        except OSError as e:
            # Best-effort cleanup: failure to close is non-fatal.
            logger.debug(
                "Failed to close file descriptor %s: %s", self._lock_fd, e
            )
        self._lock_fd = None
        if self._lockfile_path:
            try:
                self._lockfile_path.unlink(missing_ok=True)
            except OSError as e:
                # Best-effort cleanup: failure to remove lock file
                # is non-fatal.
                logger.debug(
                    "Failed to remove lock file %s: %s", self._lockfile_path, e
                )

    def _redirect_streams(self) -> None:
        sys.stdout.flush()
        sys.stderr.flush()

        stdin_fd = os.open(os.devnull, os.O_RDONLY)
        os.dup2(stdin_fd, sys.stdin.fileno())

        if self.logfile:
            log_fd = os.open(
                str(self.logfile),
                os.O_WRONLY | os.O_CREAT | os.O_APPEND,
                0o644,
            )
            os.dup2(log_fd, sys.stdout.fileno())
            os.dup2(log_fd, sys.stderr.fileno())
            if log_fd > 2:
                os.close(log_fd)
        else:
            devnull_fd = os.open(os.devnull, os.O_RDWR)
            os.dup2(devnull_fd, sys.stdout.fileno())
            os.dup2(devnull_fd, sys.stderr.fileno())
            if devnull_fd > 2:
                os.close(devnull_fd)

        if stdin_fd > 2:
            os.close(stdin_fd)

    def _setup_signal_handlers(self) -> None:
        if not self.pidfile:
            return

        original = signal.getsignal(signal.SIGHUP)

        def _handle_sighup(signum, frame):
            # Preserve pidfile identity; ensure it exists.
            self._write_pidfile()
            if callable(original):
                original(signum, frame)

        signal.signal(signal.SIGHUP, _handle_sighup)
