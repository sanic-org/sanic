from abc import ABCMeta, abstractmethod
from subprocess import Popen, PIPE
from os import path
from sys import executable
from shutil import which
from json import load
from os import kill
from signal import SIGTERM

try:
    from loguru import logger
except:
    import logging

    logger = logging.getLogger("benchmark")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.Handler(level=logging.DEBUG))


class AbstractBenchmarkRunner(metaclass=ABCMeta):
    def __init__(self, server_name):
        self._server_name = server_name
        self._command = []
        self._config = {}

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, config):
        self._config = config

    @property
    def command(self):
        return self._command

    @command.setter
    def command(self, command):
        self._command = command

    @property
    def server_name(self):
        return self._server_name

    @server_name.setter
    def server_name(self, server_name):
        self._server_name = server_name

    def __enter__(self):
        return self._enter()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._exit(exc_type, exc_val, exc_tb)

    @abstractmethod
    def _load_configuration(self):
        raise NotImplemented("Implementation Required")

    @abstractmethod
    def _enter(self):
        raise NotImplemented("Implementation Required")

    @abstractmethod
    def _exit(self, exc_type, exc_val, exc_tb):
        raise NotImplemented("Implementation Required")

    @abstractmethod
    def benchmark(self):
        raise NotImplemented("Implementation Required")

    def _run_pre_hook(self):
        if getattr(self, "_pre_run") and callable(getattr(self, "_pre_run")):
            self._pre_run()


class BoomRunner(AbstractBenchmarkRunner):
    def __init__(self, server_name):
        super(BoomRunner, self).__init__(server_name=server_name)
        self._server_process = None
        self._result = dict()

    def _pre_run(self):
        tools = ["gunicorn", "boom"]
        for tool in tools:
            if not which(tool):
                process = Popen(
                    ["pip3", "install", "--upgrade", tool],
                    stderr=PIPE,
                    stdout=PIPE,
                    stdin=PIPE,
                    close_fds=True,
                )
                out, err = process.communicate()

    def _enter(self):
        self._load_configuration()
        command = self.command
        logger.debug("Running Python Server with Command: {}".format(command))
        if command[0] == "sys.executable":
            command[0] = executable
        from subprocess import Popen, PIPE

        self._server_process = Popen(
            command,
            stdout=PIPE,
            stdin=PIPE,
            stderr=PIPE,
            close_fds=True,
            cwd=path.join(path.dirname(__file__), "servers"),
        )
        return self

    def _exit(self, exc_type, exc_val, exc_tb):
        from boom.boom import print_stats

        kill(self._server_process.pid, SIGTERM)
        print("HERE")
        for api in self._result.keys():
            print_stats(self._result.get(api))

    def benchmark(self):
        # Let's import the benchmark related stuff here to be sure it is installed.
        from boom.boom import load as benchmarker

        for api in self.config.get("apis"):
            logger.debug(
                "Running Test on API: {}".format(
                    "/".join(["http://localhost:9898", api])
                )
            )
            self._result[api] = benchmarker(
                "/".join(["http://localhost:9898", api]),
                *self.config.get("apis").get(api),
                quiet=False
            )

    def _load_configuration(self):
        config_file = path.abspath(
            path.join(path.dirname(__file__), "benchmark_config.json")
        )
        with open(config_file, "r") as fh:
            self.config = load(fh).get(self.server_name)
            self.command = self.config.get("command")


for server in ["sanic"]:
    with BoomRunner(server_name=server) as runner:
        runner.benchmark()
