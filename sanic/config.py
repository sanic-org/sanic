from inspect import isclass
from os import environ
from pathlib import Path
from typing import Any, Dict, Optional, Union
from warnings import warn

from .utils import load_module_from_file_location, str_to_bool


SANIC_PREFIX = "SANIC_"
BASE_LOGO = """

                 Sanic
         Build Fast. Run Fast.

"""

DEFAULT_CONFIG = {
    "REQUEST_MAX_SIZE": 100000000,  # 100 megabytes
    "REQUEST_BUFFER_QUEUE_SIZE": 100,
    "REQUEST_BUFFER_SIZE": 65536,  # 64 KiB
    "REQUEST_TIMEOUT": 60,  # 60 seconds
    "RESPONSE_TIMEOUT": 60,  # 60 seconds
    "KEEP_ALIVE": True,
    "KEEP_ALIVE_TIMEOUT": 5,  # 5 seconds
    "WEBSOCKET_MAX_SIZE": 2 ** 20,  # 1 megabyte
    "WEBSOCKET_MAX_QUEUE": 32,
    "WEBSOCKET_READ_LIMIT": 2 ** 16,
    "WEBSOCKET_WRITE_LIMIT": 2 ** 16,
    "WEBSOCKET_PING_TIMEOUT": 20,
    "WEBSOCKET_PING_INTERVAL": 20,
    "GRACEFUL_SHUTDOWN_TIMEOUT": 15.0,  # 15 sec
    "ACCESS_LOG": True,
    "FORWARDED_SECRET": None,
    "REAL_IP_HEADER": None,
    "PROXIES_COUNT": None,
    "FORWARDED_FOR_HEADER": "X-Forwarded-For",
    "REQUEST_ID_HEADER": "X-Request-ID",
    "FALLBACK_ERROR_FORMAT": "html",
    "REGISTER": True,
}


class Config(dict):
    def __init__(
        self,
        defaults: Dict[str, Union[str, bool, int, float, None]] = None,
        load_env: Optional[Union[bool, str]] = True,
        env_prefix: Optional[str] = SANIC_PREFIX,
        keep_alive: Optional[int] = None,
    ):
        defaults = defaults or {}
        super().__init__({**DEFAULT_CONFIG, **defaults})

        self.LOGO = BASE_LOGO

        if keep_alive is not None:
            self.KEEP_ALIVE = keep_alive

        if env_prefix != SANIC_PREFIX:
            if env_prefix:
                self.load_environment_vars(env_prefix)
        elif load_env is not True:
            if load_env:
                self.load_environment_vars(prefix=load_env)
            warn(
                "Use of load_env is deprecated and will be removed in "
                "21.12. Modify the configuration prefix by passing "
                "env_prefix instead.",
                DeprecationWarning,
            )
        else:
            self.load_environment_vars(SANIC_PREFIX)

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
        them to the configuration if present. This is called automatically when
        Sanic starts up to load environment variables into config.

        It will automatically hyrdate the following types:

        - ``int``
        - ``float``
        - ``bool``

        Anything else will be imported as a ``str``.
        """
        for k, v in environ.items():
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
        """
        Update app.config.

        .. note::

            Only upper case settings are considered

        You can upload app config by providing path to py file
        holding settings.

        .. code-block:: python

            # /some/py/file
            A = 1
            B = 2

        .. code-block:: python

            config.update_config("${some}/py/file")

        Yes you can put environment variable here, but they must be provided
        in format: ``${some_env_var}``, and mark that ``$some_env_var`` is
        treated as plain string.

        You can upload app config by providing dict holding settings.

        .. code-block:: python

            d = {"A": 1, "B": 2}
            config.update_config(d)

        You can upload app config by providing any object holding settings,
        but in such case config.__dict__ will be used as dict holding settings.

        .. code-block:: python

            class C:
                A = 1
                B = 2

            config.update_config(C)

        `See user guide re: config
        <https://sanicframework.org/guide/deployment/configuration.html>`__
        """

        if isinstance(config, (bytes, str, Path)):
            config = load_module_from_file_location(location=config)

        if not isinstance(config, dict):
            cfg = {}
            if not isclass(config):
                cfg.update(
                    {
                        key: getattr(config, key)
                        for key in config.__class__.__dict__.keys()
                    }
                )

            config = dict(config.__dict__)
            config.update(cfg)

        config = dict(filter(lambda i: i[0].isupper(), config.items()))

        self.update(config)

    load = update_config
