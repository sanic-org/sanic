from __future__ import annotations

import os
import shutil
import sys

from argparse import Namespace
from functools import partial
from textwrap import indent

from sanic.app import Sanic
from sanic.application.logo import get_logo
from sanic.cli.arguments import Group
from sanic.cli.base import SanicArgumentParser, SanicHelpFormatter
from sanic.cli.console import SanicREPL
from sanic.cli.daemon import (
    kill_daemon,
    make_kill_parser,
    make_restart_parser,
    make_status_parser,
    resolve_target,
    restart_daemon,
    status_daemon,
    stop_daemon,
)
from sanic.cli.executor import Executor, make_executor_parser
from sanic.cli.inspector import make_inspector_parser
from sanic.cli.inspector_client import InspectorClient
from sanic.compat import OS_IS_WINDOWS
from sanic.helpers import _default, is_atty
from sanic.log import error_logger
from sanic.worker.daemon import Daemon, DaemonError
from sanic.worker.loader import AppLoader


class SanicCLI:
    DESCRIPTION_SHORT = indent(
        f"""
{get_logo(True)}

Usage:
    sanic <target> [options]       Run a Sanic application
    sanic <target> exec <cmd>      Execute a command in app context
    sanic inspect [options]        Inspect a running instance
    sanic help [--full]            Show help (--full for all options)

Examples:
    sanic path.to.server:app       Run app
    sanic path.to.server --dev     Run in development mode
    sanic ./static --simple        Serve static files
""",
        prefix=" ",
    )

    DESCRIPTION_SHORT_FOOTER = """
(additional options available)

For complete options and documentation:
    sanic help --full
"""

    DESCRIPTION_FULL = indent(
        f"""
{get_logo(True)}

To start running a Sanic application, provide a path to the module, where
app is a Sanic() instance in the global scope:

    $ sanic path.to.server:app

If the Sanic instance variable is called 'app', you can leave off the last
part, and only provide a path to the module where the instance is:

    $ sanic path.to.server

Or, a path to a callable that returns a Sanic() instance:

    $ sanic path.to.factory:create_app

Or, a path to a directory to run as a simple HTTP server:

    $ sanic ./path/to/static

Additional commands:

    $ sanic inspect ...           Inspect a running Sanic instance
    $ sanic path.to.app exec ...  Run app commands
    $ sanic path.to.app status    Check if app daemon is running
    $ sanic path.to.app restart   Restart app daemon (future use)
    $ sanic path.to.app stop      Stop app daemon

Advanced daemon management:

    $ sanic kill (--pid PID | --pidfile PATH)      Force kill (SIGKILL)
    $ sanic status (--pid PID | --pidfile PATH)    Check status
    $ sanic restart (--pid PID | --pidfile PATH)   Restart (future use)
""",
        prefix=" ",
    )

    def __init__(self) -> None:
        width = shutil.get_terminal_size().columns
        self.parser = SanicArgumentParser(
            prog="sanic",
            description=self.DESCRIPTION_SHORT,
            formatter_class=lambda prog: SanicHelpFormatter(
                prog,
                max_help_position=36 if width > 96 else 24,
                indent_increment=4,
                width=None,
            ),
        )
        self.parser._positionals.title = "Required\n========\n  Positional"
        self.parser._optionals.title = "Optional\n========\n  General"
        self.main_process = (
            os.environ.get("SANIC_RELOADER_PROCESS", "") != "true"
        )
        self.args: Namespace = Namespace()
        self.groups: list[Group] = []
        self.run_mode = "serve"

    def attach(self):
        if len(sys.argv) > 1 and sys.argv[1] == "help":
            self.run_mode = "help"
            return

        if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
            self.run_mode = "help"
            return

        if len(sys.argv) > 1 and sys.argv[1] == "inspect":
            self.run_mode = "inspect"
            self.parser.description = get_logo(True)
            make_inspector_parser(self.parser)
            return

        if not OS_IS_WINDOWS and len(sys.argv) > 1 and sys.argv[1] == "kill":
            self.run_mode = "kill"
            self.parser.description = get_logo(True)
            make_kill_parser(self.parser)
            return

        if not OS_IS_WINDOWS and len(sys.argv) > 1 and sys.argv[1] == "status":
            self.run_mode = "status"
            self.parser.description = get_logo(True)
            make_status_parser(self.parser)
            return

        if (
            not OS_IS_WINDOWS
            and len(sys.argv) > 1
            and sys.argv[1] == "restart"
        ):
            self.run_mode = "restart"
            self.parser.description = get_logo(True)
            make_restart_parser(self.parser)
            return

        # Check for app-based daemon commands: sanic <app> status|restart|stop
        if (
            not OS_IS_WINDOWS
            and len(sys.argv) > 2
            and sys.argv[2]
            in (
                "status",
                "restart",
                "stop",
            )
        ):
            self.run_mode = f"app_{sys.argv[2]}"

        for group in Group._registry:
            instance = group.create(self.parser)
            instance.attach()
            self.groups.append(instance)

        if len(sys.argv) > 2 and sys.argv[2] == "exec":
            self.run_mode = "exec"
            self.parser.description = get_logo(True)
            make_executor_parser(self.parser)

    def run(self, parse_args=None):
        if self.run_mode == "inspect":
            self._inspector()
            return

        if self.run_mode == "kill":
            self._kill()
            return

        if self.run_mode == "status":
            self._status()
            return

        if self.run_mode == "restart":
            self._restart()
            return

        if self.run_mode == "help":
            self._help()
            return

        if self.run_mode.startswith("app_"):
            self._app_daemon_command()
            return

        legacy_version = False
        if not parse_args:
            # This is to provide backwards compat -v to display version
            legacy_version = len(sys.argv) == 2 and sys.argv[-1] == "-v"
            parse_args = ["--version"] if legacy_version else None
        elif parse_args == ["-v"]:
            parse_args = ["--version"]

        if not legacy_version:
            if self.run_mode == "exec":
                parse_args = [
                    a
                    for a in (parse_args or sys.argv[1:])
                    if a not in "-h --help".split()
                ]
            parsed, unknown = self.parser.parse_known_args(args=parse_args)
            if unknown and parsed.factory:
                for arg in unknown:
                    if arg.startswith("--"):
                        self.parser.add_argument(arg.split("=")[0])

        if self.run_mode == "exec":
            self.args, _ = self.parser.parse_known_args(args=parse_args)
        else:
            self.args = self.parser.parse_args(args=parse_args)
        self._precheck()
        app_loader = AppLoader(
            self.args.target, self.args.factory, self.args.simple, self.args
        )

        try:
            app = self._get_app(app_loader)
            kwargs = self._build_run_kwargs()
        except ValueError as e:
            error_logger.exception(f"Failed to run app: {e}")
        else:
            if self.run_mode == "exec":
                self._executor(app, kwargs)
                return
            elif self.run_mode != "serve":
                raise ValueError(f"Unknown run mode: {self.run_mode}")

            daemon = None
            if getattr(self.args, "daemon", False):
                daemon = self._setup_daemon(app.name)
                if daemon:
                    lines = ["Starting Sanic in daemon mode..."]
                    if daemon.pidfile:
                        lines.append(f"  PID file: {daemon.pidfile}")
                    if daemon.logfile:
                        lines.append(f"  Logs: {daemon.logfile}")
                    print("\n".join(lines), flush=True)
                    daemon.daemonize()

            if self.args.repl:
                self._repl(app)
            for http_version in self.args.http:
                app.prepare(**kwargs, version=http_version)

            if daemon:
                daemon.drop_privileges()

            if self.args.single:
                serve = Sanic.serve_single
            else:
                serve = partial(Sanic.serve, app_loader=app_loader)
            serve(app)

    def _inspector(self):
        args = sys.argv[2:]
        self.args, unknown = self.parser.parse_known_args(args=args)
        if unknown:
            for arg in unknown:
                if arg.startswith("--"):
                    try:
                        key, value = arg.split("=")
                        key = key.lstrip("-")
                    except ValueError:
                        value = False if arg.startswith("--no-") else True
                        key = (
                            arg.replace("--no-", "")
                            .lstrip("-")
                            .replace("-", "_")
                        )
                    setattr(self.args, key, value)

        kwargs = {**self.args.__dict__}
        host = kwargs.pop("host")
        port = kwargs.pop("port")
        secure = kwargs.pop("secure")
        raw = kwargs.pop("raw")
        action = kwargs.pop("action") or "info"
        api_key = kwargs.pop("api_key")
        positional = kwargs.pop("positional", None)
        if action == "<custom>" and positional:
            action = positional[0]
            if len(positional) > 1:
                kwargs["args"] = positional[1:]
        InspectorClient(host, port, secure, raw, api_key).do(action, **kwargs)

    def _kill(self):
        self.args = self.parser.parse_args(args=sys.argv[2:])
        pid, pidfile = resolve_target(self.args.pid, self.args.pidfile)
        kill_daemon(pid, pidfile)

    def _status(self):
        self.args = self.parser.parse_args(args=sys.argv[2:])
        pid, pidfile = resolve_target(self.args.pid, self.args.pidfile)
        status_daemon(pid, pidfile)

    def _restart(self):
        self.args = self.parser.parse_args(args=sys.argv[2:])
        pid, _ = resolve_target(self.args.pid, self.args.pidfile)
        restart_daemon(pid)

    def _help(self):
        full = "--full" in sys.argv
        if full:
            self.parser.description = self.DESCRIPTION_FULL
        for group in Group._registry:
            instance = group.create(self.parser)
            instance.attach(short=not full)
            self.groups.append(instance)
        self.parser.print_help()
        if not full:
            print(self.DESCRIPTION_SHORT_FOOTER)

    def _app_daemon_command(self):
        """Handle app-based daemon commands: sanic <app> status|restart|stop"""
        command = self.run_mode.replace("app_", "")
        # Parse just the app target (first arg)
        self.args = self.parser.parse_args(args=[sys.argv[1]])

        app_loader = AppLoader(
            self.args.target, self.args.factory, self.args.simple, self.args
        )

        try:
            app = self._get_app(app_loader)
        except (ImportError, ValueError) as e:
            error_logger.error(f"Failed to load app: {e}")
            sys.exit(1)

        pidfile = Daemon.get_pidfile_path(app.name)
        pid, pidfile = resolve_target(None, str(pidfile))

        if command == "status":
            status_daemon(pid, pidfile)
        elif command == "restart":
            restart_daemon(pid)
        elif command == "stop":
            force = "-f" in sys.argv or "--force" in sys.argv
            stop_daemon(pid, pidfile, force)

    def _executor(self, app: Sanic, kwargs: dict):
        args = sys.argv[3:]
        Executor(app, kwargs).run(self.args.command, args)

    def _repl(self, app: Sanic):
        if is_atty():

            @app.main_process_ready
            async def start_repl(app):
                SanicREPL(app, self.args.repl).run()
                await app._startup()

        elif self.args.repl is True:
            error_logger.error(
                "Can't start REPL in non-interactive mode. "
                "You can only run with --repl in a TTY."
            )

    def _setup_daemon(self, app_name: str):
        if OS_IS_WINDOWS:
            error_logger.error(
                "Daemon mode is not supported on Windows. "
                "Consider using a Windows service or nssm instead."
            )
            sys.exit(1)

        if getattr(self.args, "dev", False) or getattr(
            self.args, "auto_reload", False
        ):
            error_logger.error(
                "Daemon mode is not compatible with --dev or --auto-reload"
            )
            sys.exit(1)

        if getattr(self.args, "repl", False):
            error_logger.error("Daemon mode is not compatible with --repl")
            sys.exit(1)

        try:
            daemon = Daemon(
                pidfile=getattr(self.args, "pidfile", None) or "auto",
                logfile=getattr(self.args, "logfile", None),
                user=getattr(self.args, "daemon_user", None),
                group=getattr(self.args, "daemon_group", None),
                name=app_name,
            )
            return daemon
        except DaemonError as e:
            error_logger.error(f"Daemon configuration error: {e}")
            sys.exit(1)

    def _precheck(self):
        # Custom TLS mismatch handling for better diagnostics
        if self.main_process and (
            # one of cert/key missing
            bool(self.args.cert) != bool(self.args.key)
            # new and old style self.args used together
            or self.args.tls
            and self.args.cert
            # strict host checking without certs would always fail
            or self.args.tlshost
            and not self.args.tls
            and not self.args.cert
        ):
            self.parser.print_usage(sys.stderr)
            message = (
                "TLS certificates must be specified by either of:\n"
                "  --cert certdir/fullchain.pem --key certdir/privkey.pem\n"
                "  --tls certdir  (equivalent to the above)"
            )
            error_logger.error(message)
            sys.exit(1)

    def _get_app(self, app_loader: AppLoader):
        try:
            app = app_loader.load()
        except ImportError as e:
            if app_loader.module_name.startswith(e.name):  # type: ignore
                error_logger.error(
                    f"No module named {e.name} found.\n"
                    "  Example File: project/sanic_server.py -> app\n"
                    "  Example Module: project.sanic_server.app"
                )
                error_logger.error(
                    "\nThe error below might have caused the above one:\n"
                    f"{e.msg}"
                )
                sys.exit(1)
            else:
                raise e
        return app

    def _build_run_kwargs(self):
        for group in self.groups:
            group.prepare(self.args)
        ssl: None | dict | str | list = []
        if self.args.tlshost:
            ssl.append(None)
        if self.args.cert is not None or self.args.key is not None:
            ssl.append(dict(cert=self.args.cert, key=self.args.key))
        if self.args.tls:
            ssl += self.args.tls
        if not ssl:
            ssl = None
        elif len(ssl) == 1 and ssl[0] is not None:
            # Use only one cert, no TLSSelector.
            ssl = ssl[0]

        kwargs = {
            "access_log": self.args.access_log,
            "coffee": self.args.coffee,
            "debug": self.args.debug,
            "fast": self.args.fast,
            "host": self.args.host,
            "motd": self.args.motd,
            "noisy_exceptions": self.args.noisy_exceptions,
            "port": self.args.port,
            "ssl": ssl,
            "unix": self.args.unix,
            "verbosity": self.args.verbosity or 0,
            "workers": self.args.workers,
            "auto_tls": self.args.auto_tls,
            "single_process": self.args.single,
        }

        for maybe_arg in ("auto_reload", "dev"):
            if getattr(self.args, maybe_arg, False):
                kwargs[maybe_arg] = True

        if self.args.dev and all(
            arg not in sys.argv for arg in ("--repl", "--no-repl")
        ):
            self.args.repl = _default

        if self.args.path:
            kwargs["auto_reload"] = True
            kwargs["reload_dir"] = self.args.path

        return kwargs
