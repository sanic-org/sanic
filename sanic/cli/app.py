import logging
import os
import shutil
import sys

from argparse import ArgumentParser, RawTextHelpFormatter
from functools import partial
from textwrap import indent
from typing import Any, List, Union

from sanic.app import Sanic
from sanic.application.logo import get_logo
from sanic.cli.arguments import Group
from sanic.log import error_logger
from sanic.worker.inspector import inspect
from sanic.worker.loader import AppLoader


class SanicArgumentParser(ArgumentParser):
    ...


class SanicCLI:
    DESCRIPTION = indent(
        f"""
{get_logo(True)}

To start running a Sanic application, provide a path to the module, where
app is a Sanic() instance:

    $ sanic path.to.server:app

Or, a path to a callable that returns a Sanic() instance:

    $ sanic path.to.factory:create_app --factory

Or, a path to a directory to run as a simple HTTP server:

    $ sanic ./path/to/static --simple
""",
        prefix=" ",
    )

    def __init__(self) -> None:
        width = shutil.get_terminal_size().columns
        self.parser = SanicArgumentParser(
            prog="sanic",
            description=self.DESCRIPTION,
            formatter_class=lambda prog: RawTextHelpFormatter(
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
        self.args: List[Any] = []
        self.groups: List[Group] = []

    def attach(self):
        for group in Group._registry:
            instance = group.create(self.parser)
            instance.attach()
            self.groups.append(instance)

    def run(self, parse_args=None):
        legacy_version = False
        if not parse_args:
            # This is to provide backwards compat -v to display version
            legacy_version = len(sys.argv) == 2 and sys.argv[-1] == "-v"
            parse_args = ["--version"] if legacy_version else None
        elif parse_args == ["-v"]:
            parse_args = ["--version"]

        if not legacy_version:
            parsed, unknown = self.parser.parse_known_args(args=parse_args)
            if unknown and parsed.factory:
                for arg in unknown:
                    if arg.startswith("--"):
                        self.parser.add_argument(arg.split("=")[0])

        self.args = self.parser.parse_args(args=parse_args)
        self._precheck()
        app_loader = AppLoader(
            self.args.module,
            self.args.factory,
            self.args.simple,
            self.args,
        )

        try:
            app = self._get_app(app_loader)
            kwargs = self._build_run_kwargs()
        except ValueError as e:
            error_logger.exception(f"Failed to run app: {e}")
        else:
            if self.args.inspect or self.args.inspect_raw or self.args.trigger:
                os.environ["SANIC_IGNORE_PRODUCTION_WARNING"] = "true"
            else:
                for http_version in self.args.http:
                    app.prepare(**kwargs, version=http_version)

            if self.args.inspect or self.args.inspect_raw or self.args.trigger:
                action = self.args.trigger or (
                    "raw" if self.args.inspect_raw else "pretty"
                )
                inspect(
                    app.config.INSPECTOR_HOST,
                    app.config.INSPECTOR_PORT,
                    action,
                )
                del os.environ["SANIC_IGNORE_PRODUCTION_WARNING"]
                return

            if self.args.single:
                serve = Sanic.serve_single
            elif self.args.legacy:
                serve = Sanic.serve_legacy
            else:
                serve = partial(Sanic.serve, app_loader=app_loader)
            serve(app)

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
        if self.args.inspect or self.args.inspect_raw:
            logging.disable(logging.CRITICAL)

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
                sys.exit(1)
            else:
                raise e
        return app

    def _build_run_kwargs(self):
        for group in self.groups:
            group.prepare(self.args)
        ssl: Union[None, dict, str, list] = []
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
            "legacy": self.args.legacy,
        }

        for maybe_arg in ("auto_reload", "dev"):
            if getattr(self.args, maybe_arg, False):
                kwargs[maybe_arg] = True

        if self.args.path:
            kwargs["auto_reload"] = True
            kwargs["reload_dir"] = self.args.path

        return kwargs
