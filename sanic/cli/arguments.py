from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup
from typing import List, Optional, Type, Union

from sanic_routing import __version__ as __routing_version__

from sanic import __version__
from sanic.http.constants import HTTP


class Group:
    name: Optional[str]
    container: Union[ArgumentParser, _ArgumentGroup]
    _registry: List[Type[Group]] = []

    def __init_subclass__(cls) -> None:
        Group._registry.append(cls)

    def __init__(self, parser: ArgumentParser, title: Optional[str]):
        self.parser = parser

        if title:
            self.container = self.parser.add_argument_group(title=f"  {title}")
        else:
            self.container = self.parser

    @classmethod
    def create(cls, parser: ArgumentParser):
        instance = cls(parser, cls.name)
        return instance

    def add_bool_arguments(self, *args, nullable=False, **kwargs):
        group = self.container.add_mutually_exclusive_group()
        kwargs["help"] = kwargs["help"].capitalize()
        group.add_argument(*args, action="store_true", **kwargs)
        kwargs["help"] = f"no {kwargs['help'].lower()}".capitalize()
        group.add_argument(
            "--no-" + args[0][2:], *args[1:], action="store_false", **kwargs
        )
        if nullable:
            params = {args[0][2:].replace("-", "_"): None}
            group.set_defaults(**params)

    def prepare(self, args) -> None:
        ...


class GeneralGroup(Group):
    name = None

    def attach(self):
        self.container.add_argument(
            "--version",
            action="version",
            version=f"Sanic {__version__}; Routing {__routing_version__}",
        )

        self.container.add_argument(
            "module",
            help=(
                "Path to your Sanic app. Example: path.to.server:app\n"
                "If running a Simple Server, path to directory to serve. "
                "Example: ./\n"
            ),
        )


class ApplicationGroup(Group):
    name = "Application"

    def attach(self):
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
        group.add_argument(
            "--inspect",
            dest="inspect",
            action="store_true",
            help=("Inspect the state of a running instance, human readable"),
        )
        group.add_argument(
            "--inspect-raw",
            dest="inspect_raw",
            action="store_true",
            help=("Inspect the state of a running instance, JSON output"),
        )
        group.add_argument(
            "--trigger-reload",
            dest="trigger",
            action="store_const",
            const="reload",
            help=("Trigger worker processes to reload"),
        )
        group.add_argument(
            "--trigger-shutdown",
            dest="trigger",
            action="store_const",
            const="shutdown",
            help=("Trigger all processes to shutdown"),
        )


class HTTPVersionGroup(Group):
    name = "HTTP version"

    def attach(self):
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


class SocketGroup(Group):
    name = "Socket binding"

    def attach(self):
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
        self.container.add_argument(
            "-u",
            "--unix",
            dest="unix",
            type=str,
            default="",
            help="location of unix socket",
        )


class TLSGroup(Group):
    name = "TLS certificate"

    def attach(self):
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


class WorkerGroup(Group):
    name = "Worker"

    def attach(self):
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
        self.container.add_argument(
            "--legacy",
            action="store_true",
            help="Use the legacy server manager",
        )
        self.add_bool_arguments(
            "--access-logs",
            dest="access_log",
            help="display access logs",
            default=None,
        )


class DevelopmentGroup(Group):
    name = "Development"

    def attach(self):
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
            help=(
                "Watch source directory for file changes and reload on "
                "changes"
            ),
        )
        self.container.add_argument(
            "-R",
            "--reload-dir",
            dest="path",
            action="append",
            help="Extra directories to watch and reload on changes",
        )
        self.container.add_argument(
            "-d",
            "--dev",
            dest="dev",
            action="store_true",
            help=("debug + auto reload"),
        )
        self.container.add_argument(
            "--auto-tls",
            dest="auto_tls",
            action="store_true",
            help=(
                "Create a temporary TLS certificate for local development "
                "(requires mkcert or trustme)"
            ),
        )


class OutputGroup(Group):
    name = "Output"

    def attach(self):
        self.add_bool_arguments(
            "--coffee",
            dest="coffee",
            default=False,
            help="Uhm, coffee?",
        )
        self.add_bool_arguments(
            "--motd",
            dest="motd",
            default=True,
            help="Show the startup display",
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
        )
