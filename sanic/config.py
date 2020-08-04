from os import environ as os_environ
from re import findall as re_findall
from importlib.util import spec_from_file_location, \
                           module_from_spec

from typing import Union, \
                   Any


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
                            self[config_key] = strtobool(v)
                        except ValueError:
                            self[config_key] = v


    def update_config(self, config: Union[bytes, str, dict, Any]):
    """Update app.config.  
    
    Note only upper case settings are considered.  
    
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
        config.update_config(c)"""
    
        if isinstance(config, (bytes, str)):
            config = load_module_from_file_location("config", location=config)
    
        if not isinstance(config, dict):
            config = config.__dict__
    
        config = dict(filter(lambda i: i[0].isupper(), config.items()))
    
        self.update(config)


# Is in Sanic any better place where to keep this ???

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


# Is in Sanic any better place where to keep this ???

def load_module_from_file_location(*args, **kwargs):
    """Returns loaded module provided as a file path.  
    
    :param args: look for importlib.util.spec_from_file_location parameters specification  
    :param kwargs: look for importlib.util.spec_from_file_location parameters specification  
    
    So for example You can:  
    
        some_module = load_module_from_file_location("some_module_name", "/some/path/${some_env_var})  
    
    Yes you can put environment variable here, but they must be provided in format: ${some_env_var},  
    and mark that $some_env_var is treated as plain string."""
    
    # 1) Get location parameter.
    if "location" in kwargs:
        location = kwargs["location"]
        _l = "kwargs"
    elif len(args) >= 2:
        location = args[1]
        _l = "args"
    else:
        raise Exception("Provided arguments must conform to importlib.util.spec_from_file_location arguments, \
                         nonetheless location parameter has to be provided.")
    
    # 2) Parse location.
    if isinstance(location, bytes):
        location = location.decode()
    
    # A) Check if location contains any environment variables in format ${some_env_var}.
    env_vars_in_location = set(re_findall("\${(.+?)}", location))
    
    # B) Check these variables exists in environment.
    not_defined_env_vars = env_vars_in_location.difference(os_environ.keys())
    if not_defined_env_vars:
        raise Exception("There are no following environment variables: " + ", ".join(not_defined_env_vars))
    
    # C) Substitute them in location.
    for env_var in env_vars_in_location:
        location = location.replace("${" + env_var + "}", os_environ[env_var])
    
    # 3) Put back parsed location pareameter.
    if _l == "kwargs":
        kwargs["location"] = location
    else:
        _args = list(args)
        _args[1] = location
        args = tuple(_args)
    
    # 4) Load and return module.
    _mod_spec = spec_from_file_location(*args, **kwargs)
    module = module_from_spec(_mod_spec)
    _mod_spec.loader.exec_module(module)
    
    return module
