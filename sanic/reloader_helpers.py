import os
import signal
import subprocess
import sys

from multiprocessing import Process
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
    cmd = " ".join(args)
    worker_process = Process(
        target=subprocess.call,
        args=(cmd,),
        kwargs={"cwd": cwd, "shell": True, "env": new_environ},
    )
    worker_process.start()
    return worker_process


def kill_process_children_unix(pid):
    """Find and kill child processes of a process (maximum two level).

    :param pid: PID of parent process (process ID)
    :return: Nothing
    """
    root_process_path = "/proc/{pid}/task/{pid}/children".format(pid=pid)
    if not os.path.isfile(root_process_path):
        return
    with open(root_process_path) as children_list_file:
        children_list_pid = children_list_file.read().split()

    for child_pid in children_list_pid:
        children_proc_path = "/proc/%s/task/%s/children" % (
            child_pid,
            child_pid,
        )
        if not os.path.isfile(children_proc_path):
            continue
        with open(children_proc_path) as children_list_file_2:
            children_list_pid_2 = children_list_file_2.read().split()
        for _pid in children_list_pid_2:
            try:
                os.kill(int(_pid), signal.SIGTERM)
            except ProcessLookupError:
                continue
        try:
            os.kill(int(child_pid), signal.SIGTERM)
        except ProcessLookupError:
            continue


def kill_process_children_osx(pid):
    """Find and kill child processes of a process.

    :param pid: PID of parent process (process ID)
    :return: Nothing
    """
    subprocess.run(["pkill", "-P", str(pid)])


def kill_process_children(pid):
    """Find and kill child processes of a process.

    :param pid: PID of parent process (process ID)
    :return: Nothing
    """
    if sys.platform == "darwin":
        kill_process_children_osx(pid)
    elif sys.platform == "linux":
        kill_process_children_unix(pid)
    else:
        pass  # should signal error here


def kill_program_completly(proc):
    """Kill worker and it's child processes and exit.

    :param proc: worker process (process ID)
    :return: Nothing
    """
    kill_process_children(proc.pid)
    proc.terminate()
    os._exit(0)


def watchdog(sleep_interval):
    """Watch project files, restart worker process if a change happened.

    :param sleep_interval: interval in second.
    :return: Nothing
    """
    mtimes = {}
    worker_process = restart_with_reloader()
    signal.signal(
        signal.SIGTERM, lambda *args: kill_program_completly(worker_process)
    )
    signal.signal(
        signal.SIGINT, lambda *args: kill_program_completly(worker_process)
    )
    while True:
        for filename in _iter_module_files():
            try:
                mtime = os.stat(filename).st_mtime
            except OSError:
                continue

            old_time = mtimes.get(filename)
            if old_time is None:
                mtimes[filename] = mtime
                continue
            elif mtime > old_time:
                kill_process_children(worker_process.pid)
                worker_process.terminate()
                worker_process = restart_with_reloader()
                mtimes[filename] = mtime
                break

        sleep(sleep_interval)
