from os import environ as os_environ

from typing import Union, \
                   Any

from .utils import str_to_bool, \
                   load_module_from_file_location

# \/ \/ \/ \/
# TODO: remove in version: 21.3
import types
from sanic.exceptions import PyFileError
from sanic.helpers import import_string
from warnings import warn
# /\ /\ /\ /\ 



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
    "WEBSOCKET_MAX_SIZE": 2 ** 20,  # 1 megabyte
    "WEBSOCKET_MAX_QUEUE": 32,
    "WEBSOCKET_READ_LIMIT": 2 ** 16,
    "WEBSOCKET_WRITE_LIMIT": 2 ** 16,
    "GRACEFUL_SHUTDOWN_TIMEOUT": 15.0,  # 15 sec
    "ACCESS_LOG": True,
    "FORWARDED_SECRET": None,
    "REAL_IP_HEADER": None,
    "PROXIES_COUNT": None,
    "FORWARDED_FOR_HEADER": "X-Forwarded-For",
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
            raise AttributeError(f"Config has no '{ke.args[0]}'")

    def __setattr__(self, attr, value):
        self[attr] = value

    # \/ \/ \/ \/
    # TODO: remove in version: 21.3
    def from_envvar(self, variable_name):
        """Load a configuration from an environment variable pointing to
        a configuration file.

        :param variable_name: name of the environment variable
        :return: bool. ``True`` if able to load config, ``False`` otherwise.
        """

        warn("Using `from_envvar` method is deprecated and will be removed in v21.3, use `app.update_config` method instead.",
             DeprecationWarning,
             stacklevel=2)

        config_file = os_environ.get(variable_name)
        if not config_file:
            raise RuntimeError(
                "The environment variable %r is not set and "
                "thus configuration could not be loaded." % variable_name
            )
        return self.from_pyfile(config_file)
    # /\ /\ /\ /\ 

    # \/ \/ \/ \/
    # TODO: remove in version: 21.3
    def from_pyfile(self, filename):
        """Update the values in the config from a Python file.
        Only the uppercase variables in that module are stored in the config.

        :param filename: an absolute path to the config file
        """

        warn("Using `from_pyfile` method is deprecated and will be removed in v21.3, use `app.update_config` method instead.",
             DeprecationWarning,
             stacklevel=2)

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
    # /\ /\ /\ /\ 

    # \/ \/ \/ \/
    # TODO: remove in version: 21.3
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

        warn("Using `from_object` method is deprecated and will be removed in v21.3, use `app.update_config` method instead.",
             DeprecationWarning,
             stacklevel=2)

        if isinstance(obj, str):
            obj = import_string(obj)
        for key in dir(obj):
            if key.isupper():
                self[key] = getattr(obj, key)
    # /\ /\ /\ /\ 

    def load_environment_vars(self, prefix=SANIC_PREFIX):
        """
        Looks for prefixed environment variables and applies
        them to the configuration if present.
        """
        for k, v in os_environ.items():
            if k.startswith(prefix):
                _, config_key = k.split(prefix, 1)
                try:
                    self[config_key] = int(v)
                except ValueError:
                    try:
                        self[config_key] = float(v)
                    except ValueError:
                        try:
                            self[config_key] = str_to_bool(v)
                        except ValueError:
                            self[config_key] = v


    def update_config(self, config: Union[bytes, str, dict, Any]):
    """Update app.config.  
    
    Note:: only upper case settings are considered.  
    
    You can upload app config by providing path to py file holding settings.  
    
        # /some/py/file  
        A = 1  
        B = 2  
    
        config.update_config("${some}/py/file")  
    
    Yes you can put environment variable here, but they must be provided in format: ${some_env_var},  
    and mark that $some_env_var is treated as plain string.  
    
    You can upload app config by providing dict holding settings.  
    
        d = {"A": 1, "B": 2}  
        config.update_config(d)  
    
    You can upload app config by providing any object holding settings,  
    but in such case config.__dict__ will be used as dict holding settings.  
    
        class C:  
            A = 1  
            B = 2  
        config.update_config(C)"""
    
        if isinstance(config, (bytes, str)):
            config = load_module_from_file_location("config", location=config)
    
        if not isinstance(config, dict):
            config = config.__dict__
    
        config = dict(filter(lambda i: i[0].isupper(), config.items()))
    
        self.update(config)
