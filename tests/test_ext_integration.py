import pytest

from sanic import Sanic


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


def test_ext_is_loaded(stoppable_app: Sanic, sanic_ext):
    stoppable_app.run()
    sanic_ext.Extend.assert_called_once_with(stoppable_app)


def test_ext_is_not_loaded(stoppable_app: Sanic, sanic_ext):
    stoppable_app.config.AUTO_EXTEND = False
    stoppable_app.run()
    sanic_ext.Extend.assert_not_called()


def test_extend_with_args(stoppable_app: Sanic, sanic_ext):
    stoppable_app.extend(built_in_extensions=False)
    stoppable_app.run()
    sanic_ext.Extend.assert_called_once_with(
        stoppable_app, built_in_extensions=False, config=None, extensions=None
    )


def test_access_object_sets_up_extension(app: Sanic, sanic_ext):
    app.ext
    sanic_ext.Extend.assert_called_once_with(app)


def test_extend_cannot_be_called_multiple_times(app: Sanic, sanic_ext):
    app.extend()

    message = "Cannot extend Sanic after Sanic Extensions has been setup."
    with pytest.raises(RuntimeError, match=message):
        app.extend()
    sanic_ext.Extend.assert_called_once_with(
        app, extensions=None, built_in_extensions=True, config=None
    )


def test_can_access_app_ext_while_running(app: Sanic, sanic_ext, ext_instance):
    class IceCream:
        flavor: str

    @app.before_server_start
    async def injections(*_):
        app.ext.injection(IceCream)
        app.stop()

    app.run()
    ext_instance.injection.assert_called_with(IceCream)
