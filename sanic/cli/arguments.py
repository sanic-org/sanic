from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup
from typing import List, Optional, Type, Union

from sanic_routing import __version__ as __routing_version__  # type: ignore

from sanic import __version__


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

    def add_bool_arguments(self, *args, **kwargs):
        group = self.container.add_mutually_exclusive_group()
        kwargs["help"] = kwargs["help"].capitalize()
        group.add_argument(*args, action="store_true", **kwargs)
        kwargs["help"] = f"no {kwargs['help'].lower()}".capitalize()
        group.add_argument(
            "--no-" + args[0][2:], *args[1:], action="store_false", **kwargs
        )


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
        self.container.add_argument(
            "--factory",
            action="store_true",
            help=(
                "Treat app as an application factory, "
                "i.e. a () -> <Sanic app> callable"
            ),
        )
        self.container.add_argument(
            "-s",
            "--simple",
            dest="simple",
            action="store_true",
            help=(
                "Run Sanic as a Simple Server, and serve the contents of "
                "a directory\n(module arg should be a path)"
            ),
        )


class SocketGroup(Group):
    name = "Socket binding"

    def attach(self):
        self.container.add_argument(
            "-H",
            "--host",
            dest="host",
            type=str,
            default="127.0.0.1",
            help="Host address [default 127.0.0.1]",
        )
        self.container.add_argument(
            "-p",
            "--port",
            dest="port",
            type=int,
            default=8000,
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
        self.add_bool_arguments(
            "--access-logs", dest="access_log", help="display access logs"
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
            "-d",
            "--dev",
            dest="debug",
            action="store_true",
            help=(
                "Currently is an alias for --debug. But starting in v22.3, \n"
                "--debug will no longer automatically trigger auto_restart. \n"
                "However, --dev will continue, effectively making it the \n"
                "same as debug + auto_reload."
            ),
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


class OutputGroup(Group):
    name = "Output"

    def attach(self):
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
