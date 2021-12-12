import types

from importlib.util import module_from_spec, spec_from_file_location
from os import environ as os_environ
from pathlib import Path
from re import findall as re_findall
from typing import Union

from sanic.exceptions import LoadFileException, PyFileError
from sanic.helpers import import_string


def str_to_bool(val: str) -> bool:
    """Takes string and tries to turn it into bool as human would do.

    If val is in case insensitive (
        "y", "yes", "yep", "yup", "t",
        "true", "on", "enable", "enabled", "1"
    ) returns True.
    If val is in case insensitive (
        "n", "no", "f", "false", "off", "disable", "disabled", "0"
    ) returns False.
    Else Raise ValueError."""

    val = val.lower()
    if val in {
        "y",
        "yes",
        "yep",
        "yup",
        "t",
        "true",
        "on",
        "enable",
        "enabled",
        "1",
    }:
        return True
    elif val in {"n", "no", "f", "false", "off", "disable", "disabled", "0"}:
        return False
    else:
        raise ValueError(f"Invalid truth value {val}")


def load_module_from_file_location(
    location: Union[bytes, str, Path], encoding: str = "utf8", *args, **kwargs
):  # noqa
    """Returns loaded module provided as a file path.

    :param args:
        Corresponds to importlib.util.spec_from_file_location location
        parameters,but with this differences:
        - It has to be of a string or bytes type.
        - You can also use here environment variables
          in format ${some_env_var}.
          Mark that $some_env_var will not be resolved as environment variable.
    :encoding:
        If location parameter is of a bytes type, then use this encoding
        to decode it into string.
    :param args:
        Corresponds to the rest of importlib.util.spec_from_file_location
        parameters.
    :param kwargs:
        Corresponds to the rest of importlib.util.spec_from_file_location
        parameters.

    For example You can:

        some_module = load_module_from_file_location(
            "some_module_name",
            "/some/path/${some_env_var}"
        )
    """
    if isinstance(location, bytes):
        location = location.decode(encoding)

    if isinstance(location, Path) or "/" in location or "$" in location:

        if not isinstance(location, Path):
            # A) Check if location contains any environment variables
            #    in format ${some_env_var}.
            env_vars_in_location = set(re_findall(r"\${(.+?)}", location))

            # B) Check these variables exists in environment.
            not_defined_env_vars = env_vars_in_location.difference(
                os_environ.keys()
            )
            if not_defined_env_vars:
                raise LoadFileException(
                    "The following environment variables are not set: "
                    f"{', '.join(not_defined_env_vars)}"
                )

            # C) Substitute them in location.
            for env_var in env_vars_in_location:
                location = location.replace(
                    "${" + env_var + "}", os_environ[env_var]
                )

        location = str(location)
        if ".py" in location:
            name = location.split("/")[-1].split(".")[
                0
            ]  # get just the file name without path and .py extension
            _mod_spec = spec_from_file_location(
                name, location, *args, **kwargs
            )
            assert _mod_spec is not None  # type assertion for mypy
            module = module_from_spec(_mod_spec)
            _mod_spec.loader.exec_module(module)  # type: ignore

        else:
            module = types.ModuleType("config")
            module.__file__ = str(location)
            try:
                with open(location) as config_file:
                    exec(  # nosec
                        compile(config_file.read(), location, "exec"),
                        module.__dict__,
                    )
            except IOError as e:
                e.strerror = "Unable to load configuration file (e.strerror)"
                raise
            except Exception as e:
                raise PyFileError(location) from e

        return module
    else:
        try:
            return import_string(location)
        except ValueError:
            raise IOError("Unable to load configuration %s" % str(location))
