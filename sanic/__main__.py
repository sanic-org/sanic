from argparse import ArgumentParser
from importlib import import_module

from sanic.log import log
from sanic.app import Sanic

if __name__ == "__main__":
    parser = ArgumentParser(prog='sanic')
    parser.add_argument('--host', dest='host', type=str, default='127.0.0.1')
    parser.add_argument('--port', dest='port', type=int, default=8000)
    parser.add_argument('--workers', dest='workers', type=int, default=1, )
    parser.add_argument('--debug', dest='debug', action="store_true")
    parser.add_argument('module')
    args = parser.parse_args()

    try:
        module_parts = args.module.split(".")
        module_name = ".".join(module_parts[:-1])
        app_name = module_parts[-1]

        module = import_module(module_name)
        app = getattr(module, app_name, None)
        if not isinstance(app, Sanic):
            raise ValueError("Module is not a Sanic app, it is a {}.  "
                             "Perhaps you meant {}.app?"
                             .format(type(app).__name__, args.module))

        app.run(host=args.host, port=args.port,
                workers=args.workers, debug=args.debug)
    except ImportError:
        log.error("No module named {} found.\n"
                  "  Example File: project/sanic_server.py -> app\n"
                  "  Example Module: project.sanic_server.app"
                  .format(module_name))
    except ValueError as e:
        log.error("{}".format(e))
