import logging
import os

from contextlib import contextmanager
from os import environ
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent
from unittest.mock import Mock, call

import pytest

from pytest import MonkeyPatch

from sanic import Sanic
from sanic.config import DEFAULT_CONFIG, Config
from sanic.constants import LocalCertCreator
from sanic.exceptions import PyFileError


@contextmanager
def temp_path():
    """a simple cross platform replacement for NamedTemporaryFile"""
    with TemporaryDirectory() as td:
        yield Path(td, "file")


class ConfigTest:
    not_for_config = "should not be used"
    CONFIG_VALUE = "should be used"

    @property
    def ANOTHER_VALUE(self):
        return self.CONFIG_VALUE

    @property
    def another_not_for_config(self):
        return self.not_for_config


class UltimateAnswer:
    def __init__(self, answer):
        self.answer = int(answer)


def test_load_from_object(app: Sanic):
    app.config.load(ConfigTest)
    assert "CONFIG_VALUE" in app.config
    assert app.config.CONFIG_VALUE == "should be used"
    assert "not_for_config" not in app.config


def test_load_from_object_string(app: Sanic):
    app.config.load("tests.test_config.ConfigTest")
    assert "CONFIG_VALUE" in app.config
    assert app.config.CONFIG_VALUE == "should be used"
    assert "not_for_config" not in app.config


def test_load_from_instance(app: Sanic):
    app.config.load(ConfigTest())
    assert "CONFIG_VALUE" in app.config
    assert app.config.CONFIG_VALUE == "should be used"
    assert app.config.ANOTHER_VALUE == "should be used"
    assert "not_for_config" not in app.config
    assert "another_not_for_config" not in app.config


def test_load_from_object_string_exception(app: Sanic):
    with pytest.raises(ImportError):
        app.config.load("test_config.Config.test")


def test_auto_env_prefix():
    environ["SANIC_TEST_ANSWER"] = "42"
    app = Sanic(name="Test")
    assert app.config.TEST_ANSWER == 42
    del environ["SANIC_TEST_ANSWER"]


def test_auto_bool_env_prefix():
    environ["SANIC_TEST_ANSWER"] = "True"
    app = Sanic(name="Test")
    assert app.config.TEST_ANSWER is True
    del environ["SANIC_TEST_ANSWER"]


@pytest.mark.parametrize("env_prefix", [None, ""])
def test_empty_load_env_prefix(env_prefix):
    environ["SANIC_TEST_ANSWER"] = "42"
    app = Sanic(name="Test", env_prefix=env_prefix)
    assert getattr(app.config, "TEST_ANSWER", None) is None
    del environ["SANIC_TEST_ANSWER"]


def test_env_prefix():
    environ["MYAPP_TEST_ANSWER"] = "42"
    app = Sanic(name="Test", env_prefix="MYAPP_")
    assert app.config.TEST_ANSWER == 42
    del environ["MYAPP_TEST_ANSWER"]


def test_env_prefix_float_values():
    environ["MYAPP_TEST_ROI"] = "2.3"
    app = Sanic(name="Test", env_prefix="MYAPP_")
    assert app.config.TEST_ROI == 2.3
    del environ["MYAPP_TEST_ROI"]


def test_env_prefix_string_value():
    environ["MYAPP_TEST_TOKEN"] = "somerandomtesttoken"
    app = Sanic(name="Test", env_prefix="MYAPP_")
    assert app.config.TEST_TOKEN == "somerandomtesttoken"
    del environ["MYAPP_TEST_TOKEN"]


def test_env_w_custom_converter():
    environ["SANIC_TEST_ANSWER"] = "42"

    config = Config(converters=[UltimateAnswer])
    app = Sanic(name="Test", config=config)
    assert isinstance(app.config.TEST_ANSWER, UltimateAnswer)
    assert app.config.TEST_ANSWER.answer == 42
    del environ["SANIC_TEST_ANSWER"]


def test_env_lowercase():
    environ["SANIC_test_answer"] = "42"
    app = Sanic(name="Test")
    assert "test_answer" not in app.config
    del environ["SANIC_test_answer"]


def test_add_converter_multiple_times(caplog):
    def converter():
        ...

    message = (
        "Configuration value converter 'converter' has already been registered"
    )
    config = Config()
    config.register_type(converter)
    with caplog.at_level(logging.WARNING):
        config.register_type(converter)

    assert ("sanic.error", logging.WARNING, message) in caplog.record_tuples
    assert len(config._converters) == 5


def test_load_from_file(app: Sanic):
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
        app.config.load(str(config_path))
        assert "VALUE" in app.config
        assert app.config.VALUE == "some value"
        assert "CONDITIONAL" in app.config
        assert app.config.CONDITIONAL == "should be set"
        assert "condition" not in app.config


def test_load_from_missing_file(app: Sanic):
    with pytest.raises(IOError):
        app.config.load("non-existent file")


def test_load_from_envvar(app: Sanic):
    config = "VALUE = 'some value'"
    with temp_path() as config_path:
        config_path.write_text(config)
        environ["APP_CONFIG"] = str(config_path)
        app.config.load("${APP_CONFIG}")
        assert "VALUE" in app.config
        assert app.config.VALUE == "some value"


def test_load_from_missing_envvar(app: Sanic):
    with pytest.raises(IOError) as e:
        app.config.load("non-existent variable")
        assert str(e.value) == (
            "The environment variable 'non-existent "
            "variable' is not set and thus configuration "
            "could not be loaded."
        )


def test_load_config_from_file_invalid_syntax(app: Sanic):
    config = "VALUE = some value"
    with temp_path() as config_path:
        config_path.write_text(config)

        with pytest.raises(PyFileError):
            app.config.load(config_path)


def test_overwrite_exisiting_config(app: Sanic):
    app.config.DEFAULT = 1

    class Config:
        DEFAULT = 2

    app.config.load(Config)
    assert app.config.DEFAULT == 2


def test_overwrite_exisiting_config_ignore_lowercase(app: Sanic):
    app.config.default = 1

    class Config:
        default = 2

    app.config.load(Config)
    assert app.config.default == 1


def test_missing_config(app: Sanic):
    with pytest.raises(AttributeError, match="Config has no 'NON_EXISTENT'"):
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
    we should have all the variables from defaults rewriting them with
    custom defaults passed in
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
    test that environment variables has higher priority than DEFAULT_CONFIG
    and passed defaults dict
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


@pytest.mark.parametrize("access_log", (True, False))
def test_config_access_log_passing_in_run(app: Sanic, access_log):
    assert app.config.ACCESS_LOG is False

    @app.listener("after_server_start")
    async def _request(sanic, loop):
        app.stop()

    app.run(port=1340, access_log=access_log, single_process=True)
    assert app.config.ACCESS_LOG is access_log


@pytest.mark.asyncio
async def test_config_access_log_passing_in_create_server(app: Sanic):
    assert app.config.ACCESS_LOG is False

    @app.listener("after_server_start")
    async def _request(sanic, loop):
        app.stop()

    await app.create_server(
        port=1341, access_log=False, return_asyncio_server=True
    )
    assert app.config.ACCESS_LOG is False

    await app.create_server(
        port=1342, access_log=True, return_asyncio_server=True
    )
    assert app.config.ACCESS_LOG is True


def test_config_rewrite_keep_alive():
    config = Config()
    assert config.KEEP_ALIVE == DEFAULT_CONFIG["KEEP_ALIVE"]
    config = Config(keep_alive=True)
    assert config.KEEP_ALIVE is True
    config = Config(keep_alive=False)
    assert config.KEEP_ALIVE is False

    # use defaults
    config = Config(defaults={"KEEP_ALIVE": False})
    assert config.KEEP_ALIVE is False
    config = Config(defaults={"KEEP_ALIVE": True})
    assert config.KEEP_ALIVE is True


_test_setting_as_dict = {"TEST_SETTING_VALUE": 1}
_test_setting_as_class = type("C", (), {"TEST_SETTING_VALUE": 1})
_test_setting_as_module = str(
    Path(__file__).parent / "static/app_test_config.py"
)


@pytest.mark.parametrize(
    "conf_object",
    [
        _test_setting_as_dict,
        _test_setting_as_class,
        _test_setting_as_module,
    ],
    ids=["from_dict", "from_class", "from_file"],
)
def test_update(app: Sanic, conf_object):
    app.update_config(conf_object)
    assert app.config["TEST_SETTING_VALUE"] == 1


def test_update_from_lowercase_key(app: Sanic):
    d = {"test_setting_value": 1}
    app.update_config(d)
    assert "test_setting_value" not in app.config


def test_config_set_methods(app: Sanic, monkeypatch: MonkeyPatch):
    post_set = Mock()
    monkeypatch.setattr(Config, "_post_set", post_set)

    app.config.FOO = 1
    post_set.assert_called_once_with("FOO", 1)
    post_set.reset_mock()

    app.config["FOO"] = 2
    post_set.assert_called_once_with("FOO", 2)
    post_set.reset_mock()

    app.config.update({"FOO": 3})
    post_set.assert_called_once_with("FOO", 3)
    post_set.reset_mock()

    app.config.update([("FOO", 4)])
    post_set.assert_called_once_with("FOO", 4)
    post_set.reset_mock()

    app.config.update(FOO=5)
    post_set.assert_called_once_with("FOO", 5)
    post_set.reset_mock()

    app.config.update({"FOO": 6}, {"BAR": 7})
    post_set.assert_has_calls(
        calls=[
            call("FOO", 6),
            call("BAR", 7),
        ]
    )
    post_set.reset_mock()

    app.config.update({"FOO": 8}, BAR=9)
    post_set.assert_has_calls(
        calls=[
            call("FOO", 8),
            call("BAR", 9),
        ],
        any_order=True,
    )
    post_set.reset_mock()

    app.config.update_config({"FOO": 10})
    post_set.assert_called_once_with("FOO", 10)


def test_negative_proxy_count(app: Sanic):
    app.config.PROXIES_COUNT = -1

    message = (
        "PROXIES_COUNT cannot be negative. "
        "https://sanic.readthedocs.io/en/latest/sanic/config.html"
        "#proxy-configuration"
    )
    with pytest.raises(ValueError, match=message):
        app.prepare()


@pytest.mark.parametrize(
    "passed,expected",
    (
        ("auto", LocalCertCreator.AUTO),
        ("mkcert", LocalCertCreator.MKCERT),
        ("trustme", LocalCertCreator.TRUSTME),
        ("AUTO", LocalCertCreator.AUTO),
        ("MKCERT", LocalCertCreator.MKCERT),
        ("TRUSTME", LocalCertCreator.TRUSTME),
    ),
)
def test_convert_local_cert_creator(passed, expected):
    os.environ["SANIC_LOCAL_CERT_CREATOR"] = passed
    app = Sanic("Test")
    assert app.config.LOCAL_CERT_CREATOR is expected
    del os.environ["SANIC_LOCAL_CERT_CREATOR"]
