from __future__ import annotations

from inspect import getmembers, isclass, isdatadescriptor
from os import environ
from pathlib import Path
from typing import Any, Dict, Optional, Union
from warnings import warn

from sanic.errorpages import DEFAULT_FORMAT, check_error_format
from sanic.helpers import _default
from sanic.http import Http
from sanic.log import error_logger
from sanic.utils import load_module_from_file_location, str_to_bool


SANIC_PREFIX = "SANIC_"


DEFAULT_CONFIG = {
    "_FALLBACK_ERROR_FORMAT": _default,
    "ACCESS_LOG": True,
    "AUTO_RELOAD": False,
    "EVENT_AUTOREGISTER": False,
    "FORWARDED_FOR_HEADER": "X-Forwarded-For",
    "FORWARDED_SECRET": None,
    "GRACEFUL_SHUTDOWN_TIMEOUT": 15.0,  # 15 sec
    "KEEP_ALIVE_TIMEOUT": 5,  # 5 seconds
    "KEEP_ALIVE": True,
    "MOTD": True,
    "MOTD_DISPLAY": {},
    "NOISY_EXCEPTIONS": False,
    "PROXIES_COUNT": None,
    "REAL_IP_HEADER": None,
    "REGISTER": True,
    "REQUEST_BUFFER_SIZE": 65536,  # 64 KiB
    "REQUEST_MAX_HEADER_SIZE": 8192,  # 8 KiB, but cannot exceed 16384
    "REQUEST_ID_HEADER": "X-Request-ID",
    "REQUEST_MAX_SIZE": 100000000,  # 100 megabytes
    "REQUEST_TIMEOUT": 60,  # 60 seconds
    "RESPONSE_TIMEOUT": 60,  # 60 seconds
    "WEBSOCKET_MAX_SIZE": 2 ** 20,  # 1 megabyte
    "WEBSOCKET_PING_INTERVAL": 20,
    "WEBSOCKET_PING_TIMEOUT": 20,
}


class DescriptorMeta(type):
    def __init__(cls, *_):
        cls.__setters__ = {name for name, _ in getmembers(cls, cls._is_setter)}

    @staticmethod
    def _is_setter(member: object):
        return isdatadescriptor(member) and hasattr(member, "setter")


class Config(dict, metaclass=DescriptorMeta):
    ACCESS_LOG: bool
    AUTO_RELOAD: bool
    EVENT_AUTOREGISTER: bool
    FORWARDED_FOR_HEADER: str
    FORWARDED_SECRET: Optional[str]
    GRACEFUL_SHUTDOWN_TIMEOUT: float
    KEEP_ALIVE_TIMEOUT: int
    KEEP_ALIVE: bool
    NOISY_EXCEPTIONS: bool
    MOTD: bool
    MOTD_DISPLAY: Dict[str, str]
    PROXIES_COUNT: Optional[int]
    REAL_IP_HEADER: Optional[str]
    REGISTER: bool
    REQUEST_BUFFER_SIZE: int
    REQUEST_MAX_HEADER_SIZE: int
    REQUEST_ID_HEADER: str
    REQUEST_MAX_SIZE: int
    REQUEST_TIMEOUT: int
    RESPONSE_TIMEOUT: int
    SERVER_NAME: str
    WEBSOCKET_MAX_SIZE: int
    WEBSOCKET_PING_INTERVAL: int
    WEBSOCKET_PING_TIMEOUT: int

    def __init__(
        self,
        defaults: Dict[str, Union[str, bool, int, float, None]] = None,
        load_env: Optional[Union[bool, str]] = True,
        env_prefix: Optional[str] = SANIC_PREFIX,
        keep_alive: Optional[bool] = None,
    ):
        defaults = defaults or {}
        super().__init__({**DEFAULT_CONFIG, **defaults})

        self._LOGO = ""

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

        self._configure_header_size()
        self._check_error_format()
        self._init = True

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError as ke:
            raise AttributeError(f"Config has no '{ke.args[0]}'")

    def __setattr__(self, attr, value) -> None:
        if attr in self.__class__.__setters__:
            try:
                super().__setattr__(attr, value)
            except AttributeError:
                ...
            else:
                return None
        self.update({attr: value})

    def __setitem__(self, attr, value) -> None:
        self.update({attr: value})

    def update(self, *other, **kwargs) -> None:
        other_mapping = {k: v for item in other for k, v in dict(item).items()}
        super().update(*other, **kwargs)
        for attr, value in {**other_mapping, **kwargs}.items():
            self._post_set(attr, value)

    def _post_set(self, attr, value) -> None:
        if self.get("_init"):
            if attr in (
                "REQUEST_MAX_HEADER_SIZE",
                "REQUEST_BUFFER_SIZE",
                "REQUEST_MAX_SIZE",
            ):
                self._configure_header_size()
            elif attr == "LOGO":
                self._LOGO = value
                warn(
                    "Setting the config.LOGO is deprecated and will no longer "
                    "be supported starting in v22.6.",
                    DeprecationWarning,
                )

    @property
    def LOGO(self):
        return self._LOGO

    @property
    def FALLBACK_ERROR_FORMAT(self) -> str:
        if self._FALLBACK_ERROR_FORMAT is _default:
            return DEFAULT_FORMAT
        return self._FALLBACK_ERROR_FORMAT

    @FALLBACK_ERROR_FORMAT.setter
    def FALLBACK_ERROR_FORMAT(self, value):
        self._check_error_format(value)
        if (
            self._FALLBACK_ERROR_FORMAT is not _default
            and value != self._FALLBACK_ERROR_FORMAT
        ):
            error_logger.warning(
                "Setting config.FALLBACK_ERROR_FORMAT on an already "
                "configured value may have unintended consequences."
            )
        self._FALLBACK_ERROR_FORMAT = value

    def _configure_header_size(self):
        Http.set_header_max_size(
            self.REQUEST_MAX_HEADER_SIZE,
            self.REQUEST_BUFFER_SIZE - 4096,
            self.REQUEST_MAX_SIZE,
        )

    def _check_error_format(self, format: Optional[str] = None):
        check_error_format(format or self.FALLBACK_ERROR_FORMAT)

    def load_environment_vars(self, prefix=SANIC_PREFIX):
        """
        Looks for prefixed environment variables and applies them to the
        configuration if present. This is called automatically when Sanic
        starts up to load environment variables into config.

        It will automatically hydrate the following types:

        - ``int``
        - ``float``
        - ``bool``

        Anything else will be imported as a ``str``.
        """
        for key, value in environ.items():
            if not key.startswith(prefix):
                continue

            _, config_key = key.split(prefix, 1)

            for converter in (int, float, str_to_bool, str):
                try:
                    self[config_key] = converter(value)
                    break
                except ValueError:
                    pass

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
