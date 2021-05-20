import os
import sys

from argparse import ArgumentParser, RawDescriptionHelpFormatter
from importlib import import_module
from typing import Any, Dict, Optional

from sanic_routing import __version__ as __routing_version__  # type: ignore

from sanic import __version__
from sanic.app import Sanic
from sanic.config import BASE_LOGO
from sanic.log import error_logger


class SanicArgumentParser(ArgumentParser):
    def add_bool_arguments(self, *args, **kwargs):
        group = self.add_mutually_exclusive_group()
        group.add_argument(*args, action="store_true", **kwargs)
        kwargs["help"] = "no " + kwargs["help"]
        group.add_argument(
            "--no-" + args[0][2:], *args[1:], action="store_false", **kwargs
        )


def main():
    parser = SanicArgumentParser(
        prog="sanic",
        description=BASE_LOGO,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-H",
        "--host",
        dest="host",
        type=str,
        default="127.0.0.1",
        help="host address [default 127.0.0.1]",
    )
    parser.add_argument(
        "-p",
        "--port",
        dest="port",
        type=int,
        default=8000,
        help="port to serve on [default 8000]",
    )
    parser.add_argument(
        "-u",
        "--unix",
        dest="unix",
        type=str,
        default="",
        help="location of unix socket",
    )
    parser.add_argument(
        "--cert", dest="cert", type=str, help="location of certificate for SSL"
    )
    parser.add_argument(
        "--key", dest="key", type=str, help="location of keyfile for SSL."
    )
    parser.add_argument(
        "-w",
        "--workers",
        dest="workers",
        type=int,
        default=1,
        help="number of worker processes [default 1]",
    )
    parser.add_argument("-d", "--debug", dest="debug", action="store_true")
    parser.add_argument(
        "-r",
        "--auto-reload",
        dest="auto_reload",
        action="store_true",
        help="Watch source directory for file changes and reload on changes",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"Sanic {__version__}; Routing {__routing_version__}",
    )
    parser.add_bool_arguments(
        "--access-logs", dest="access_log", help="display access logs"
    )
    parser.add_argument(
        "module", help="path to your Sanic app. Example: path.to.server:app"
    )
    args = parser.parse_args()

    try:
        module_path = os.path.abspath(os.getcwd())
        if module_path not in sys.path:
            sys.path.append(module_path)

        delimiter = ":" if ":" in args.module else "."
        module_name, app_name = args.module.rsplit(delimiter, 1)

        module = import_module(module_name)
        app = getattr(module, app_name, None)
        app_name = type(app).__name__

        if not isinstance(app, Sanic):
            raise ValueError(
                f"Module is not a Sanic app, it is a {app_name}.  "
                f"Perhaps you meant {args.module}.app?"
            )
        if args.cert is not None or args.key is not None:
            ssl: Optional[Dict[str, Any]] = {
                "cert": args.cert,
                "key": args.key,
            }
        else:
            ssl = None

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
