from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup

from sanic_routing import __version__ as __routing_version__

from sanic import __version__
from sanic.compat import OS_IS_WINDOWS
from sanic.http.constants import HTTP


class Group:
    name: str | None
    container: ArgumentParser | _ArgumentGroup
    _registry: list[type[Group]] = []

    def __init_subclass__(cls) -> None:
        Group._registry.append(cls)

    def __init__(self, parser: ArgumentParser, title: str | None):
        self.parser = parser

        if title:
            self.container = self.parser.add_argument_group(title=f"  {title}")
        else:
            self.container = self.parser

    @classmethod
    def create(cls, parser: ArgumentParser):
        instance = cls(parser, cls.name)
        return instance

    def add_bool_arguments(
        self,
        *args,
        nullable=False,
        help: str,
        negative_help: str | None = None,
        **kwargs,
    ):
        group = self.container.add_mutually_exclusive_group()

        pos_help = help[0].upper() + help[1:]
        neg_help = (
            negative_help if negative_help else f"Disable {help.lower()}"
        )

        group.add_argument(
            *args,
            action="store_true",
            help=pos_help,
            **kwargs,
        )

        group.add_argument(
            "--no-" + args[0][2:],
            *args[1:],
            action="store_false",
            help=neg_help[0].upper() + neg_help[1:],
            **kwargs,
        )

        if nullable:
            group.set_defaults(**{args[0][2:].replace("-", "_"): None})

    def prepare(self, args) -> None: ...

    def attach(self, short: bool = False) -> None: ...


class GeneralGroup(Group):
    name = None

    def attach(self, short: bool = False):
        if short:
            return

        self.container.add_argument(
            "--version",
            action="version",
            version=f"Sanic {__version__}; Routing {__routing_version__}",
        )

        self.container.add_argument(
            "target",
            help=(
                "Path to your Sanic app instance.\n"
                "\tExample: path.to.server:app\n"
                "If running a Simple Server, path to directory to serve.\n"
                "\tExample: ./\n"
                "Additionally, this can be a path to a factory function\n"
                "that returns a Sanic app instance.\n"
                "\tExample: path.to.server:create_app\n"
            ),
        )

        choices = ["serve", "exec"]
        help_text = (
            "Action to perform.\n"
            "\tserve: Run the Sanic app [default]\n"
            "\texec: Execute a command in the Sanic app context\n"
        )
        if not OS_IS_WINDOWS:
            choices.extend(["status", "restart", "stop"])
            help_text += (
                "\tstatus: Check if daemon is running\n"
                "\trestart: Restart daemon (future use)\n"
                "\tstop: Stop daemon gracefully\n"
            )
        self.container.add_argument(
            "action",
            nargs="?",
            default="serve",
            choices=choices,
            help=help_text,
        )


class ApplicationGroup(Group):
    name = "Application"

    def attach(self, short: bool = False):
        if short:
            return

        group = self.container.add_mutually_exclusive_group()
        group.add_argument(
            "--factory",
            action="store_true",
            help=(
                "Treat app as an application factory, "
                "i.e. a () -> <Sanic app> callable"
            ),
        )
        group.add_argument(
            "-s",
            "--simple",
            dest="simple",
            action="store_true",
            help=(
                "Run Sanic as a Simple Server, and serve the contents of "
                "a directory\n(module arg should be a path)"
            ),
        )
        self.add_bool_arguments(
            "--repl",
            help="Run with an interactive shell session",
            negative_help="Disable interactive shell session",
        )


class SocketGroup(Group):
    name = "Socket binding"

    def attach(self, short: bool = False):
        self.container.add_argument(
            "-H",
            "--host",
            dest="host",
            type=str,
            help="Host address [default 127.0.0.1]",
        )
        self.container.add_argument(
            "-p",
            "--port",
            dest="port",
            type=int,
            help="Port to serve on [default 8000]",
        )
        if not OS_IS_WINDOWS and not short:
            self.container.add_argument(
                "-u",
                "--unix",
                dest="unix",
                type=str,
                default="",
                help="location of UNIX socket",
            )


class HTTPVersionGroup(Group):
    name = "HTTP version"

    def attach(self, short: bool = False):
        if short:
            return

        http_values = [http.value for http in HTTP.__members__.values()]

        self.container.add_argument(
            "--http",
            dest="http",
            action="append",
            choices=http_values,
            type=int,
            help=(
                "Which HTTP version to use: HTTP/1.1 or HTTP/3. Value should\n"
                "be either 1, or 3. [default 1]"
            ),
        )
        self.container.add_argument(
            "-1",
            dest="http",
            action="append_const",
            const=1,
            help=("Run Sanic server using HTTP/1.1"),
        )
        self.container.add_argument(
            "-3",
            dest="http",
            action="append_const",
            const=3,
            help=("Run Sanic server using HTTP/3"),
        )

    def prepare(self, args):
        if not args.http:
            args.http = [1]
        args.http = tuple(sorted(set(map(HTTP, args.http)), reverse=True))


class TLSGroup(Group):
    name = "TLS certificate"

    def attach(self, short: bool = False):
        if short:
            return

        self.container.add_argument(
            "--cert",
            dest="cert",
            type=str,
            help="Location of fullchain.pem, bundle.crt or equivalent",
        )
        self.container.add_argument(
            "--key",
            dest="key",
            type=str,
            help="Location of privkey.pem or equivalent .key file",
        )
        self.container.add_argument(
            "--tls",
            metavar="DIR",
            type=str,
            action="append",
            help=(
                "TLS certificate folder with fullchain.pem and privkey.pem\n"
                "May be specified multiple times to choose multiple "
                "certificates"
            ),
        )
        self.container.add_argument(
            "--tls-strict-host",
            dest="tlshost",
            action="store_true",
            help="Only allow clients that send an SNI matching server certs",
        )


class DevelopmentGroup(Group):
    name = "Development"

    def attach(self, short: bool = False):
        if not short:
            self.container.add_argument(
                "--debug",
                dest="debug",
                action="store_true",
                help="Run the server in debug mode",
            )
            self.container.add_argument(
                "-r",
                "--reload",
                "--auto-reload",
                dest="auto_reload",
                action="store_true",
                help="Auto-reload on source changes",
            )
            self.container.add_argument(
                "-R",
                "--reload-dir",
                dest="path",
                action="append",
                help="Additional directories to watch for changes",
            )
        self.container.add_argument(
            "-d",
            "--dev",
            dest="dev",
            action="store_true",
            help="Run in development mode (debug + auto-reload)",
        )
        if not short:
            self.container.add_argument(
                "--auto-tls",
                dest="auto_tls",
                action="store_true",
                help=(
                    "Create a temporary TLS certificate for local development "
                    "(requires mkcert or trustme)"
                ),
            )


class WorkerGroup(Group):
    name = "Worker"

    def attach(self, short: bool = False):
        if short:
            return

        group = self.container.add_mutually_exclusive_group()
        group.add_argument(
            "-w",
            "--workers",
            dest="workers",
            type=int,
            default=1,
            help="Number of worker processes [default 1]",
        )
        group.add_argument(
            "--fast",
            dest="fast",
            action="store_true",
            help="Set the number of workers to max allowed",
        )
        group.add_argument(
            "--single-process",
            dest="single",
            action="store_true",
            help="Do not use multiprocessing, run server in a single process",
        )
        self.add_bool_arguments(
            "--access-logs",
            dest="access_log",
            help="display access logs",
            default=None,
        )


class OutputGroup(Group):
    name = "Output"

    def attach(self, short: bool = False):
        if short:
            return

        self.add_bool_arguments(
            "--coffee",
            dest="coffee",
            default=False,
            help="Uhm, coffee?",
            negative_help="No coffee? Is that a typo?",
        )
        self.add_bool_arguments(
            "--motd",
            dest="motd",
            default=True,
            help="Show the startup display",
            negative_help="Disable the startup display",
        )
        self.container.add_argument(
            "-v",
            "--verbosity",
            action="count",
            help="Control logging noise, eg. -vv or --verbosity=2 [default 0]",
        )
        self.add_bool_arguments(
            "--noisy-exceptions",
            dest="noisy_exceptions",
            help="Output stack traces for all exceptions",
            default=None,
        )


class DaemonGroup(Group):
    name = "Daemon"

    def attach(self, short: bool = False):
        if OS_IS_WINDOWS:
            return

        self.container.add_argument(
            "-D",
            "--daemon",
            dest="daemon",
            action="store_true",
            help="Run server in background (auto-generated PID file)",
        )

        if short:
            return

        self.container.add_argument(
            "--pidfile",
            dest="pidfile",
            type=str,
            default=None,
            help="Override auto-generated PID file path (requires --daemon)",
        )
        self.container.add_argument(
            "--logfile",
            dest="logfile",
            type=str,
            default=None,
            help="Path to log file for daemon output (requires --daemon)",
        )
        self.container.add_argument(
            "--user",
            dest="daemon_user",
            type=str,
            default=None,
            help="User to run daemon as (requires root)",
        )
        self.container.add_argument(
            "--group",
            dest="daemon_group",
            type=str,
            default=None,
            help="Group to run daemon as (requires root)",
        )

    def prepare(self, args):
        if OS_IS_WINDOWS:
            return

        has_daemon_opts = getattr(args, "pidfile", None) or getattr(
            args, "logfile", None
        )
        if has_daemon_opts and not getattr(args, "daemon", False):
            raise SystemExit("Error: --pidfile and --logfile require --daemon")
