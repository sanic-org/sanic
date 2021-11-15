import sys

from unittest.mock import MagicMock

import pytest

from sanic import Sanic
from sanic.exceptions import SanicException


try:
    import sanic_ext

    SANIC_EXT_IN_ENV = True
except ImportError:
    SANIC_EXT_IN_ENV = False


@pytest.fixture
def stoppable_app(app):
    @app.before_server_start
    async def stop(*_):
        app.stop()

    return app


@pytest.fixture
def ext_instance():
    ext_instance = MagicMock()
    ext_instance.injection = MagicMock()
    return ext_instance


@pytest.fixture  # type: ignore
def sanic_ext(ext_instance):  # noqa
    sanic_ext = MagicMock(__version__="1.2.3")
    sanic_ext.Extend = MagicMock()
    sanic_ext.Extend.return_value = ext_instance
    sys.modules["sanic_ext"] = sanic_ext
    yield sanic_ext
    del sys.modules["sanic_ext"]


def test_ext_is_loaded(stoppable_app: Sanic, sanic_ext):
    stoppable_app.run()
    sanic_ext.Extend.assert_called_once_with(stoppable_app)


def test_extend_with_args(stoppable_app: Sanic, sanic_ext):
    stoppable_app.extend(built_in_extensions=False)
    stoppable_app.run()
    sanic_ext.Extend.assert_called_once_with(
        stoppable_app, built_in_extensions=False, config=None, extensions=None
    )


@pytest.mark.skipif(
    SANIC_EXT_IN_ENV,
    reason="Running tests with sanic_ext already in the environment",
)
def test_fail_if_not_loaded(app: Sanic):
    with pytest.raises(
        RuntimeError, match="Sanic Extensions is not installed.*"
    ):
        app.extend(built_in_extensions=False)


def test_cannot_access_app_ext_if_not_running(app: Sanic):
    with pytest.raises(
        SanicException,
        match="Cannot access Sanic.ext property while Sanic is not running.",
    ):
        app.ext


def test_can_access_app_ext_while_running(app: Sanic, sanic_ext, ext_instance):
    class IceCream:
        flavor: str

    @app.before_server_start
    async def injections(*_):
        app.ext.injection(IceCream)
        app.stop()

    app.run()
    ext_instance.injection.assert_called_with(IceCream)
