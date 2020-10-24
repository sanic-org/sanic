import os
import sys

from argparse import ArgumentParser
from importlib import import_module
from typing import Any, Dict, Optional

from sanic.app import Sanic
from sanic.log import logger


def main():
    parser = ArgumentParser(prog="sanic")
    parser.add_argument("--host", dest="host", type=str, default="127.0.0.1")
    parser.add_argument("--port", dest="port", type=int, default=8000)
    parser.add_argument("--unix", dest="unix", type=str, default="")
    parser.add_argument(
        "--cert", dest="cert", type=str, help="location of certificate for SSL"
    )
    parser.add_argument(
        "--key", dest="key", type=str, help="location of keyfile for SSL."
    )
    parser.add_argument("--workers", dest="workers", type=int, default=1)
    parser.add_argument("--debug", dest="debug", action="store_true")
    parser.add_argument("module")
    args = parser.parse_args()

    try:
        module_path = os.path.abspath(os.getcwd())
        if module_path not in sys.path:
            sys.path.append(module_path)

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
