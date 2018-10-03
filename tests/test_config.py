from os import environ
import pytest
from tempfile import NamedTemporaryFile

from sanic import Sanic
from sanic.exceptions import PyFileError


def test_load_from_object(app):
    class Config:
        not_for_config = 'should not be used'
        CONFIG_VALUE = 'should be used'

    app.config.from_object(Config)
    assert 'CONFIG_VALUE' in app.config
    assert app.config.CONFIG_VALUE == 'should be used'
    assert 'not_for_config' not in app.config


def test_auto_load_env():
    environ["SANIC_TEST_ANSWER"] = "42"
    app = Sanic()
    assert app.config.TEST_ANSWER == 42
    del environ["SANIC_TEST_ANSWER"]


def test_dont_load_env():
    environ["SANIC_TEST_ANSWER"] = "42"
    app = Sanic(load_env=False)
    assert getattr(app.config, 'TEST_ANSWER', None) is None
    del environ["SANIC_TEST_ANSWER"]


def test_load_env_prefix():
    environ["MYAPP_TEST_ANSWER"] = "42"
    app = Sanic(load_env='MYAPP_')
    assert app.config.TEST_ANSWER == 42
    del environ["MYAPP_TEST_ANSWER"]


def test_load_from_file(app):
    config = b"""
VALUE = 'some value'
condition = 1 == 1
if condition:
    CONDITIONAL = 'should be set'
    """
    with NamedTemporaryFile() as config_file:
        config_file.write(config)
        config_file.seek(0)
        app.config.from_pyfile(config_file.name)
        assert 'VALUE' in app.config
        assert app.config.VALUE == 'some value'
        assert 'CONDITIONAL' in app.config
        assert app.config.CONDITIONAL == 'should be set'
        assert 'condition' not in app.config


def test_load_from_missing_file(app):
    with pytest.raises(IOError):
        app.config.from_pyfile('non-existent file')


def test_load_from_envvar(app):
    config = b"VALUE = 'some value'"
    with NamedTemporaryFile() as config_file:
        config_file.write(config)
        config_file.seek(0)
        environ['APP_CONFIG'] = config_file.name
        app.config.from_envvar('APP_CONFIG')
        assert 'VALUE' in app.config
        assert app.config.VALUE == 'some value'


def test_load_from_missing_envvar(app):
    with pytest.raises(RuntimeError) as e:
        app.config.from_envvar('non-existent variable')
        assert str(e.value) == ("The environment variable 'non-existent "
                                "variable' is not set and thus configuration "
                                "could not be loaded.")


def test_load_config_from_file_invalid_syntax(app):
    config = b"VALUE = some value"
    with NamedTemporaryFile() as config_file:
        config_file.write(config)
        config_file.seek(0)

        with pytest.raises(PyFileError):
            app.config.from_pyfile(config_file.name)


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
    with pytest.raises(AttributeError) as e:
        app.config.NON_EXISTENT
        assert str(e.value) == ("Config has no 'NON_EXISTENT'")
