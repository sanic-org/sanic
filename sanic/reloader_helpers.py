import os
import signal
import subprocess
import sys

from time import sleep


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
    rv = [sys.executable]
    main_module = sys.modules["__main__"]
    mod_spec = getattr(main_module, "__spec__", None)
    if mod_spec:
        # Parent exe was launched as a module rather than a script
        rv.extend(["-m", mod_spec.name])
        if len(sys.argv) > 1:
            rv.extend(sys.argv[1:])
    else:
        rv.extend(sys.argv)
    return rv


def restart_with_reloader():
    """Create a new process and a subprocess in it with the same arguments as
    this one.
    """
    cwd = os.getcwd()
    args = _get_args_for_reloading()
    new_environ = os.environ.copy()
    new_environ["SANIC_SERVER_RUNNING"] = "true"
    return subprocess.Popen(args, cwd=cwd, env=new_environ)

def join(worker_process):
    try:
        # Graceful
        worker_process.terminate()
        worker_process.wait(2)
    except subprocess.TimeoutExpired:
        # Not so graceful
        try:
            worker_process.terminate()
            worker_process.wait(1)
        except subprocess.TimeoutExpired:
            worker_process.kill()
            worker_process.wait()

def watchdog(sleep_interval):
    """Watch project files, restart worker process if a change happened.

    :param sleep_interval: interval in second.
    :return: Nothing
    """
    try:
        mtimes = {}
        worker_process = restart_with_reloader()
        quit = False
        def terminate(sig, frame):
            nonlocal quit
            quit = True
            worker_process.terminate()
        signal.signal(signal.SIGTERM, terminate)
        signal.signal(signal.SIGINT, terminate)
        while not quit:
            for i in range(10):
                sleep(sleep_interval / 10)
                if quit or worker_process.poll():
                    return

            need_reload = False

            for filename in _iter_module_files():
                try:
                    mtime = os.stat(filename).st_mtime
                except OSError:
                    continue

                old_time = mtimes.get(filename)
                if old_time is None:
                    mtimes[filename] = mtime
                elif mtime > old_time:
                    mtimes[filename] = mtime
                    need_reload = True

            if need_reload:
                worker_process.terminate()
                sleep(0.1)
                worker_process = restart_with_reloader()

    finally:
        join(worker_process)
