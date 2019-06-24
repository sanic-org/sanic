import os
import types

from sanic.exceptions import PyFileError
from sanic.helpers import import_string


SANIC_PREFIX = "SANIC_"
BASE_LOGO = """

                 Sanic
         Build Fast. Run Fast.

"""

DEFAULT_CONFIG = {
    "REQUEST_MAX_SIZE": 100000000,  # 100 megabytes
    "REQUEST_BUFFER_QUEUE_SIZE": 100,
    "REQUEST_TIMEOUT": 60,  # 60 seconds
    "RESPONSE_TIMEOUT": 60,  # 60 seconds
    "KEEP_ALIVE": True,
    "KEEP_ALIVE_TIMEOUT": 5,  # 5 seconds
    "WEBSOCKET_MAX_SIZE": 2 ** 20,  # 1 megabytes
    "WEBSOCKET_MAX_QUEUE": 32,
    "WEBSOCKET_READ_LIMIT": 2 ** 16,
    "WEBSOCKET_WRITE_LIMIT": 2 ** 16,
    "GRACEFUL_SHUTDOWN_TIMEOUT": 15.0,  # 15 sec
    "ACCESS_LOG": True,
    "PROXIES_COUNT": -1,
    "FORWARDED_FOR_HEADER": "X-Forwarded-For",
    "REAL_IP_HEADER": "X-Real-IP",
}


class Config(dict):
    def __init__(self, defaults=None, load_env=True, keep_alive=None):
        defaults = defaults or {}
        super().__init__({**DEFAULT_CONFIG, **defaults})

        self.LOGO = BASE_LOGO

        if keep_alive is not None:
            self.KEEP_ALIVE = keep_alive

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
                exec(  # nosec
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

            or also:
            app.config.from_object('myproject.config.MyConfigClass')

        You should not use this function to load the actual configuration but
        rather configuration defaults. The actual config should be loaded
        with :meth:`from_pyfile` and ideally from a location not within the
        package because the package might be installed system wide.

        :param obj: an object holding the configuration
        """
        if isinstance(obj, str):
            obj = import_string(obj)
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
                        try:
                            self[config_key] = strtobool(v)
                        except ValueError:
                            self[config_key] = v


def strtobool(val):
    """
    This function was borrowed from distutils.utils. While distutils
    is part of stdlib, it feels odd to use distutils in main application code.

    The function was modified to walk its talk and actually return bool
    and not int.
    """
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    elif val in ("n", "no", "f", "false", "off", "0"):
        return False
    else:
        raise ValueError("invalid truth value %r" % (val,))
