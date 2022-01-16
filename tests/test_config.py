from contextlib import contextmanager
from os import environ
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent

import pytest

from sanic import Sanic
from sanic.config import DEFAULT_CONFIG, Config
from sanic.exceptions import PyFileError


@contextmanager
def temp_path():
    """a simple cross platform replacement for NamedTemporaryFile"""
    with TemporaryDirectory() as td:
        yield Path(td, "file")


class ConfigTest:
    not_for_config = "should not be used"
    CONFIG_VALUE = "should be used"


def test_load_from_object(app):
    app.config.from_object(ConfigTest)
    assert "CONFIG_VALUE" in app.config
    assert app.config.CONFIG_VALUE == "should be used"
    assert "not_for_config" not in app.config


def test_load_from_object_string(app):
    app.config.from_object("test_config.ConfigTest")
    assert "CONFIG_VALUE" in app.config
    assert app.config.CONFIG_VALUE == "should be used"
    assert "not_for_config" not in app.config


def test_load_from_object_string_exception(app):
    with pytest.raises(ImportError):
        app.config.from_object("test_config.Config.test")


def test_auto_load_env():
    environ["SANIC_TEST_ANSWER"] = "42"
    app = Sanic(name=__name__)
    assert app.config.TEST_ANSWER == 42
    del environ["SANIC_TEST_ANSWER"]


def test_auto_load_bool_env():
    environ["SANIC_TEST_ANSWER"] = "True"
    app = Sanic(name=__name__)
    assert app.config.TEST_ANSWER == True
    del environ["SANIC_TEST_ANSWER"]


def test_dont_load_env():
    environ["SANIC_TEST_ANSWER"] = "42"
    app = Sanic(name=__name__, load_env=False)
    assert getattr(app.config, "TEST_ANSWER", None) is None
    del environ["SANIC_TEST_ANSWER"]


def test_load_env_prefix():
    environ["MYAPP_TEST_ANSWER"] = "42"
    app = Sanic(name=__name__, load_env="MYAPP_")
    assert app.config.TEST_ANSWER == 42
    del environ["MYAPP_TEST_ANSWER"]


def test_load_env_prefix_float_values():
    environ["MYAPP_TEST_ROI"] = "2.3"
    app = Sanic(name=__name__, load_env="MYAPP_")
    assert app.config.TEST_ROI == 2.3
    del environ["MYAPP_TEST_ROI"]


def test_load_env_prefix_string_value():
    environ["MYAPP_TEST_TOKEN"] = "somerandomtesttoken"
    app = Sanic(name=__name__, load_env="MYAPP_")
    assert app.config.TEST_TOKEN == "somerandomtesttoken"
    del environ["MYAPP_TEST_TOKEN"]


def test_load_from_file(app):
    config = dedent(
        """
    VALUE = 'some value'
    condition = 1 == 1
    if condition:
        CONDITIONAL = 'should be set'
    """
    )
    with temp_path() as config_path:
        config_path.write_text(config)
        app.config.from_pyfile(str(config_path))
        assert "VALUE" in app.config
        assert app.config.VALUE == "some value"
        assert "CONDITIONAL" in app.config
        assert app.config.CONDITIONAL == "should be set"
        assert "condition" not in app.config


def test_load_from_missing_file(app):
    with pytest.raises(IOError):
        app.config.from_pyfile("non-existent file")


def test_load_from_envvar(app):
    config = "VALUE = 'some value'"
    with temp_path() as config_path:
        config_path.write_text(config)
        environ["APP_CONFIG"] = str(config_path)
        app.config.from_envvar("APP_CONFIG")
        assert "VALUE" in app.config
        assert app.config.VALUE == "some value"


def test_load_from_missing_envvar(app):
    with pytest.raises(RuntimeError) as e:
        app.config.from_envvar("non-existent variable")
        assert str(e.value) == (
            "The environment variable 'non-existent "
            "variable' is not set and thus configuration "
            "could not be loaded."
        )


def test_load_config_from_file_invalid_syntax(app):
    config = "VALUE = some value"
    with temp_path() as config_path:
        config_path.write_text(config)

        with pytest.raises(PyFileError):
            app.config.from_pyfile(config_path)


def test_overwrite_exisiting_config(app):
    app.config.DEFAULT = 1

    class Config:
        DEFAULT = 2

    app.config.from_object(Config)
    assert app.config.DEFAULT == 2


def test_overwrite_exisiting_config_ignore_lowercase(app):
    app.config.default = 1

    class Config:
        default = 2

    app.config.from_object(Config)
    assert app.config.default == 1


def test_missing_config(app):
    with pytest.raises(
        AttributeError, match="Config has no 'NON_EXISTENT'"
    ) as e:
        _ = app.config.NON_EXISTENT


def test_config_defaults():
    """
    load DEFAULT_CONFIG
    """
    conf = Config()
    for key, value in DEFAULT_CONFIG.items():
        assert getattr(conf, key) == value


def test_config_custom_defaults():
    """
    we should have all the variables from defaults rewriting them with custom defaults passed in
    Config
    """
    custom_defaults = {
        "REQUEST_MAX_SIZE": 1,
        "KEEP_ALIVE": False,
        "ACCESS_LOG": False,
    }
    conf = Config(defaults=custom_defaults)
    for key, value in DEFAULT_CONFIG.items():
        if key in custom_defaults.keys():
            value = custom_defaults[key]
        assert getattr(conf, key) == value


def test_config_custom_defaults_with_env():
    """
    test that environment variables has higher priority than DEFAULT_CONFIG and passed defaults dict
    """
    custom_defaults = {
        "REQUEST_MAX_SIZE123": 1,
        "KEEP_ALIVE123": False,
        "ACCESS_LOG123": False,
    }

    environ_defaults = {
        "SANIC_REQUEST_MAX_SIZE123": "2",
        "SANIC_KEEP_ALIVE123": "True",
        "SANIC_ACCESS_LOG123": "False",
    }

    for key, value in environ_defaults.items():
        environ[key] = value

    conf = Config(defaults=custom_defaults)
    for key, value in DEFAULT_CONFIG.items():
        if "SANIC_" + key in environ_defaults.keys():
            value = environ_defaults["SANIC_" + key]
            try:
                value = int(value)
            except ValueError:
                if value in ["True", "False"]:
                    value = value == "True"

        assert getattr(conf, key) == value

    for key, value in environ_defaults.items():
        del environ[key]


def test_config_access_log_passing_in_run(app):
    assert app.config.ACCESS_LOG == True

    @app.listener("after_server_start")
    async def _request(sanic, loop):
        app.stop()

    app.run(port=1340, access_log=False)
    assert app.config.ACCESS_LOG == False

    app.run(port=1340, access_log=True)
    assert app.config.ACCESS_LOG == True


@pytest.mark.asyncio
async def test_config_access_log_passing_in_create_server(app):
    assert app.config.ACCESS_LOG == True

    @app.listener("after_server_start")
    async def _request(sanic, loop):
        app.stop()

    await app.create_server(
        port=1341, access_log=False, return_asyncio_server=True
    )
    assert app.config.ACCESS_LOG == False

    await app.create_server(
        port=1342, access_log=True, return_asyncio_server=True
    )
    assert app.config.ACCESS_LOG == True


def test_config_rewrite_keep_alive():
    config = Config()
    assert config.KEEP_ALIVE == DEFAULT_CONFIG["KEEP_ALIVE"]
    config = Config(keep_alive=True)
    assert config.KEEP_ALIVE == True
    config = Config(keep_alive=False)
    assert config.KEEP_ALIVE == False

    # use defaults
    config = Config(defaults={"KEEP_ALIVE": False})
    assert config.KEEP_ALIVE == False
    config = Config(defaults={"KEEP_ALIVE": True})
    assert config.KEEP_ALIVE == True
