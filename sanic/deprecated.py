# NOTE (tomaszdrozdz): remove in version: 21.3
import types
from sanic.exceptions import PyFileError
from sanic.helpers import import_string
from warnings import warn
# END remove in version: 21.3



# NOTE (tomaszdrozdz): remove in version: 21.3

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

# END remove in version: 21.3
