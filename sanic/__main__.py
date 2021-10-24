import os
import sys

from argparse import ArgumentParser, RawTextHelpFormatter
from importlib import import_module
from pathlib import Path
from typing import Union

from sanic_routing import __version__ as __routing_version__  # type: ignore

from sanic import __version__
from sanic.app import Sanic
from sanic.config import BASE_LOGO
from sanic.log import error_logger
from sanic.simple import create_simple_server


class SanicArgumentParser(ArgumentParser):
    def add_bool_arguments(self, *args, **kwargs):
        group = self.add_mutually_exclusive_group()
        group.add_argument(*args, action="store_true", **kwargs)
        kwargs["help"] = f"no {kwargs['help']}\n "
        group.add_argument(
            "--no-" + args[0][2:], *args[1:], action="store_false", **kwargs
        )


def main():
    parser = SanicArgumentParser(
        prog="sanic",
        description=BASE_LOGO,
        formatter_class=lambda prog: RawTextHelpFormatter(
            prog, max_help_position=33
        ),
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"Sanic {__version__}; Routing {__routing_version__}",
    )
    parser.add_argument(
        "--factory",
        action="store_true",
        help=(
            "Treat app as an application factory, "
            "i.e. a () -> <Sanic app> callable"
        ),
    )
    parser.add_argument(
        "-s",
        "--simple",
        dest="simple",
        action="store_true",
        help="Run Sanic as a Simple Server (module arg should be a path)\n ",
    )
    parser.add_argument(
        "-H",
        "--host",
        dest="host",
        type=str,
        default="127.0.0.1",
        help="Host address [default 127.0.0.1]",
    )
    parser.add_argument(
        "-p",
        "--port",
        dest="port",
        type=int,
        default=8000,
        help="Port to serve on [default 8000]",
    )
    parser.add_argument(
        "-u",
        "--unix",
        dest="unix",
        type=str,
        default="",
        help="location of unix socket\n ",
    )
    parser.add_argument(
        "--cert",
        dest="cert",
        type=str,
        help="Location of certificate (instead of --tls)",
    )
    parser.add_argument(
        "--key",
        dest="key",
        type=str,
        help="Location of keyfile (instead of --tls)",
    )
    parser.add_argument(
        "--tls",
        metavar="DIR",
        type=str,
        action="append",
        help="TLS certificate folder with fullchain.pem and privkey.pem.\n"
        "May be specified multiple times to choose of multiple certificates.",
    )
    parser.add_argument(
        "--tls-strict-host",
        dest="tlshost",
        action="store_true",
        help="Only allow clients that send an SNI matching server certs.\n ",
    )
    parser.add_bool_arguments(
        "--access-logs", dest="access_log", help="display access logs"
    )
    parser.add_argument(
        "-w",
        "--workers",
        dest="workers",
        type=int,
        default=1,
        help="number of worker processes [default 1]\n ",
    )
    parser.add_argument("-d", "--debug", dest="debug", action="store_true")
    parser.add_argument(
        "-r",
        "--reload",
        "--auto-reload",
        dest="auto_reload",
        action="store_true",
        help="Watch source directory for file changes and reload on changes",
    )
    parser.add_argument(
        "-R",
        "--reload-dir",
        dest="path",
        action="append",
        help="Extra directories to watch and reload on changes\n ",
    )
    parser.add_argument(
        "module",
        help=(
            "Path to your Sanic app. Example: path.to.server:app\n"
            "If running a Simple Server, path to directory to serve. "
            "Example: ./\n"
        ),
    )
    args = parser.parse_args()

    try:
        module_path = os.path.abspath(os.getcwd())
        if module_path not in sys.path:
            sys.path.append(module_path)

        if args.simple:
            path = Path(args.module)
            app = create_simple_server(path)
        else:
            delimiter = ":" if ":" in args.module else "."
            module_name, app_name = args.module.rsplit(delimiter, 1)

            if app_name.endswith("()"):
                args.factory = True
                app_name = app_name[:-2]

            module = import_module(module_name)
            app = getattr(module, app_name, None)
            if args.factory:
                app = app()

            app_type_name = type(app).__name__

            if not isinstance(app, Sanic):
                raise ValueError(
                    f"Module is not a Sanic app, it is a {app_type_name}.  "
                    f"Perhaps you meant {args.module}.app?"
                )
        ssl: Union[None, dict, str, list] = []
        if args.tlshost:
            ssl.append(None)
        if args.cert is not None or args.key is not None:
            ssl.append(dict(cert=args.cert, key=args.key))
        if args.tls:
            ssl += args.tls
        if not ssl:
            ssl = None
        elif len(ssl) == 1 and ssl[0] is not None:
            # Use only one cert, no TLSSelector.
            ssl = ssl[0]
        kwargs = {
            "host": args.host,
            "port": args.port,
            "unix": args.unix,
            "workers": args.workers,
            "debug": args.debug,
            "access_log": args.access_log,
            "ssl": ssl,
        }
        if args.auto_reload:
            kwargs["auto_reload"] = True

        if args.path:
            if args.auto_reload or args.debug:
                kwargs["reload_dir"] = args.path
            else:
                error_logger.warning(
                    "Ignoring '--reload-dir' since auto reloading was not "
                    "enabled. If you would like to watch directories for "
                    "changes, consider using --debug or --auto-reload."
                )

        app.run(**kwargs)
    except ImportError as e:
        if module_name.startswith(e.name):
            error_logger.error(
                f"No module named {e.name} found.\n"
                "  Example File: project/sanic_server.py -> app\n"
                "  Example Module: project.sanic_server.app"
            )
        else:
            raise e
    except ValueError:
        error_logger.exception("Failed to run app")


if __name__ == "__main__":
    main()
