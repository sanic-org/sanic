import os
import sys

from argparse import ArgumentParser, RawDescriptionHelpFormatter
from importlib import import_module
from typing import Any, Dict, Optional

from sanic import __version__
from sanic.app import Sanic
from sanic.config import BASE_LOGO
from sanic.log import logger


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
    parser.add_argument("--debug", dest="debug", action="store_true")
    parser.add_bool_arguments(
        "--access-logs", dest="access_log", help="display access logs"
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"Sanic {__version__}",
    )
    parser.add_argument(
        "module", help="path to your Sanic app. Example: path.to.server:app"
    )
    args = parser.parse_args()

    try:
        module_path = os.path.abspath(os.getcwd())
        if module_path not in sys.path:
            sys.path.append(module_path)

        if ":" in args.module:
            module_name, app_name = args.module.rsplit(":", 1)
        else:
            module_parts = args.module.split(".")
            module_name = ".".join(module_parts[:-1])
            app_name = module_parts[-1]

        module = import_module(module_name)
        app = getattr(module, app_name, None)
        app_name = type(app).__name__

        if not isinstance(app, Sanic):
            raise ValueError(
                f"Module is not a Sanic app, it is a {app_name}.  "
                f"Perhaps you meant {args.module}.app?"
            )
        if args.cert is not None or args.key is not None:
            ssl = {
                "cert": args.cert,
                "key": args.key,
            }  # type: Optional[Dict[str, Any]]
        else:
            ssl = None

        app.run(
            host=args.host,
            port=args.port,
            unix=args.unix,
            workers=args.workers,
            debug=args.debug,
            access_log=args.access_log,
            ssl=ssl,
        )
    except ImportError as e:
        logger.error(
            f"No module named {e.name} found.\n"
            f"  Example File: project/sanic_server.py -> app\n"
            f"  Example Module: project.sanic_server.app"
        )
    except ValueError:
        logger.exception("Failed to run app")


if __name__ == "__main__":
    main()
