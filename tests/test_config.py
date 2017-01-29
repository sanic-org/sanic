from os import environ
import pytest
from tempfile import NamedTemporaryFile

from sanic import Sanic


def test_load_from_object():
    app = Sanic('test_load_from_object')
    class Config:
        not_for_config = 'should not be used'
        CONFIG_VALUE = 'should be used'

    app.config.from_object(Config)
    assert 'CONFIG_VALUE' in app.config
    assert app.config.CONFIG_VALUE == 'should be used'
    assert 'not_for_config' not in app.config


def test_load_from_file():
    app = Sanic('test_load_from_file')
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


def test_load_from_missing_file():
    app = Sanic('test_load_from_missing_file')
    with pytest.raises(IOError):
        app.config.from_pyfile('non-existent file')


def test_load_from_envvar():
    app = Sanic('test_load_from_envvar')
    config = b"VALUE = 'some value'"
    with NamedTemporaryFile() as config_file:
        config_file.write(config)
        config_file.seek(0)
        environ['APP_CONFIG'] = config_file.name
        app.config.from_envvar('APP_CONFIG')
        assert 'VALUE' in app.config
        assert app.config.VALUE == 'some value'


def test_load_from_missing_envvar():
    app = Sanic('test_load_from_missing_envvar')
    with pytest.raises(RuntimeError):
        app.config.from_envvar('non-existent variable')


def test_overwrite_exisiting_config():
    app = Sanic('test_overwrite_exisiting_config')
    app.config.DEFAULT = 1
    class Config:
        DEFAULT = 2

    app.config.from_object(Config)
    assert app.config.DEFAULT == 2


def test_missing_config():
    app = Sanic('test_missing_config')
    with pytest.raises(AttributeError):
        app.config.NON_EXISTENT
