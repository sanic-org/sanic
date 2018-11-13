import os
import types

from sanic.exceptions import PyFileError


SANIC_PREFIX = "SANIC_"


class Config(dict):
    def __init__(self, defaults=None, load_env=True, keep_alive=True):
        super().__init__(defaults or {})
        self.LOGO = """
                 ▄▄▄▄▄
        ▀▀▀██████▄▄▄       _______________
      ▄▄▄▄▄  █████████▄  /                 \\
     ▀▀▀▀█████▌ ▀▐▄ ▀▐█ |   Gotta go fast!  |
   ▀▀█████▄▄ ▀██████▄██ | _________________/
   ▀▄▄▄▄▄  ▀▀█▄▀█════█▀ |/
        ▀▀▀▄  ▀▀███ ▀       ▄▄
     ▄███▀▀██▄████████▄ ▄▀▀▀▀▀▀█▌
   ██▀▄▄▄██▀▄███▀ ▀▀████      ▄██
▄▀▀▀▄██▄▀▀▌████▒▒▒▒▒▒███     ▌▄▄▀
▌    ▐▀████▐███▒▒▒▒▒▐██▌
▀▄▄▄▄▀   ▀▀████▒▒▒▒▄██▀
          ▀▀█████████▀
        ▄▄██▀██████▀█
      ▄██▀     ▀▀▀  █
     ▄█             ▐▌
 ▄▄▄▄█▌              ▀█▄▄▄▄▀▀▄
▌     ▐                ▀▀▄▄▄▀
 ▀▀▄▄▀
"""
        self.REQUEST_MAX_SIZE = 100000000  # 100 megabytes
        self.REQUEST_TIMEOUT = 60  # 60 seconds
        self.RESPONSE_TIMEOUT = 60  # 60 seconds
        self.KEEP_ALIVE = keep_alive
        self.KEEP_ALIVE_TIMEOUT = 5  # 5 seconds
        self.WEBSOCKET_MAX_SIZE = 2 ** 20  # 1 megabytes
        self.WEBSOCKET_MAX_QUEUE = 32
        self.WEBSOCKET_READ_LIMIT = 2 ** 16
        self.WEBSOCKET_WRITE_LIMIT = 2 ** 16
        self.GRACEFUL_SHUTDOWN_TIMEOUT = 15.0  # 15 sec
        self.ACCESS_LOG = True

        if load_env:
            prefix = SANIC_PREFIX if load_env is True else load_env
            self.load_environment_vars(prefix=prefix)

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError as ke:
            raise AttributeError("Config has no '{}'".format(ke.args[0]))

    def __setattr__(self, attr, value):
        self[attr] = value

    def from_envvar(self, variable_name):
        """Load a configuration from an environment variable pointing to
        a configuration file.

        :param variable_name: name of the environment variable
        :return: bool. ``True`` if able to load config, ``False`` otherwise.
        """
        config_file = os.environ.get(variable_name)
        if not config_file:
            raise RuntimeError(
                "The environment variable %r is not set and "
                "thus configuration could not be loaded." % variable_name
            )
        return self.from_pyfile(config_file)

    def from_pyfile(self, filename):
        """Update the values in the config from a Python file.
        Only the uppercase variables in that module are stored in the config.

        :param filename: an absolute path to the config file
        """
        module = types.ModuleType("config")
        module.__file__ = filename
        try:
            with open(filename) as config_file:
                exec(
                    compile(config_file.read(), filename, "exec"),
                    module.__dict__,
                )
        except IOError as e:
            e.strerror = "Unable to load configuration file (%s)" % e.strerror
            raise
        except Exception as e:
            raise PyFileError(filename) from e

        self.from_object(module)
        return True

    def from_object(self, obj):
        """Update the values from the given object.
        Objects are usually either modules or classes.

        Just the uppercase variables in that object are stored in the config.
        Example usage::

            from yourapplication import default_config
            app.config.from_object(default_config)

        You should not use this function to load the actual configuration but
        rather configuration defaults. The actual config should be loaded
        with :meth:`from_pyfile` and ideally from a location not within the
        package because the package might be installed system wide.

        :param obj: an object holding the configuration
        """
        for key in dir(obj):
            if key.isupper():
                self[key] = getattr(obj, key)

    def load_environment_vars(self, prefix=SANIC_PREFIX):
        """
        Looks for prefixed environment variables and applies
        them to the configuration if present.
        """
        for k, v in os.environ.items():
            if k.startswith(prefix):
                _, config_key = k.split(prefix, 1)
                try:
                    self[config_key] = int(v)
                except ValueError:
                    try:
                        self[config_key] = float(v)
                    except ValueError:
                        self[config_key] = v
