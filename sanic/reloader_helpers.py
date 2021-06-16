import os
import signal
import subprocess
import sys

from pathlib import Path
from time import sleep

from sanic.config import BASE_LOGO
from sanic.log import logger


def _iter_module_files():
    """This iterates over all relevant Python files.

    It goes through all
    loaded files from modules, all files in folders of already loaded modules
    as well as all files reachable through a package.
    """
    # The list call is necessary on Python 3 in case the module
    # dictionary modifies during iteration.
    for module in list(sys.modules.values()):
        if module is None:
            continue
        filename = getattr(module, "__file__", None)
        if filename:
            old = None
            while not os.path.isfile(filename):
                old = filename
                filename = os.path.dirname(filename)
                if filename == old:
                    break
            else:
                if filename[-4:] in (".pyc", ".pyo"):
                    filename = filename[:-1]
                yield filename


def _get_args_for_reloading():
    """Returns the executable."""
    main_module = sys.modules["__main__"]
    mod_spec = getattr(main_module, "__spec__", None)
    if sys.argv[0] in ("", "-c"):
        raise RuntimeError(
            f"Autoreloader cannot work with argv[0]={sys.argv[0]!r}"
        )
    if mod_spec:
        # Parent exe was launched as a module rather than a script
        return [sys.executable, "-m", mod_spec.name] + sys.argv[1:]
    return [sys.executable] + sys.argv


def restart_with_reloader():
    """Create a new process and a subprocess in it with the same arguments as
    this one.
    """
    return subprocess.Popen(
        _get_args_for_reloading(),
        env={**os.environ, "SANIC_SERVER_RUNNING": "true"},
    )


def _check_file(filename, mtimes):
    need_reload = False

    mtime = os.stat(filename).st_mtime
    old_time = mtimes.get(filename)
    if old_time is None:
        mtimes[filename] = mtime
    elif mtime > old_time:
        mtimes[filename] = mtime
        need_reload = True

    return need_reload


def watchdog(sleep_interval, app):
    """Watch project files, restart worker process if a change happened.

    :param sleep_interval: interval in second.
    :return: Nothing
    """

    def interrupt_self(*args):
        raise KeyboardInterrupt

    mtimes = {}
    signal.signal(signal.SIGTERM, interrupt_self)
    if os.name == "nt":
        signal.signal(signal.SIGBREAK, interrupt_self)

    worker_process = restart_with_reloader()

    if app.config.LOGO:
        logger.debug(
            app.config.LOGO if isinstance(app.config.LOGO, str) else BASE_LOGO
        )

    try:
        while True:
            need_reload = False

            for collection in (_iter_module_files(), *app.reload_dirs):
                if isinstance(collection, Path):
                    collection = collection.glob("**/*")

                for filename in collection:
                    try:
                        check = _check_file(filename, mtimes)
                    except OSError:
                        continue

                    if check:
                        need_reload = True
                        break

                if need_reload:
                    break

            if need_reload:
                worker_process.terminate()
                worker_process.wait()
                worker_process = restart_with_reloader()

            sleep(sleep_interval)
    except KeyboardInterrupt:
        pass
    finally:
        worker_process.terminate()
        worker_process.wait()
