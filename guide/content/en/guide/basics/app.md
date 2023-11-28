# Sanic Application

See API docs: [sanic.app](/api/sanic.app)

## Instance

.. column::

    The most basic building block is the :class:`sanic.app.Sanic` instance. It is not required, but the custom is to instantiate this in a file called `server.py`.

.. column::

    ```python
    # /path/to/server.py

    from sanic import Sanic

    app = Sanic("MyHelloWorldApp")
    ```

## Application context

Most applications will have the need to share/reuse data or objects across different parts of the code base. Sanic helps be providing the `ctx` object on application instances. It is a free space for the developer to attach any objects or data that should existe throughout the lifetime of the application.


.. column::

    The most common pattern is to attach a database instance to the application.

.. column::

    ```python
    app = Sanic("MyApp")
    app.ctx.db = Database()
    ```


.. column::

    While the previous example will work and is illustrative, it is typically considered best practice to attach objects in one of the two application startup [listeners](./listeners).

.. column::

    ```python
    app = Sanic("MyApp")

    @app.before_server_start
    async def attach_db(app, loop):
        app.ctx.db = Database()
    ```


## App Registry

.. column::

    When you instantiate a Sanic instance, that can be retrieved at a later time from the Sanic app registry. This can be useful, for example, if you need to access your Sanic instance from a location where it is not otherwise accessible.

.. column::

    ```python
    # ./path/to/server.py
    from sanic import Sanic

    app = Sanic("my_awesome_server")

    # ./path/to/somewhere_else.py
    from sanic import Sanic

    app = Sanic.get_app("my_awesome_server")
    ```


.. column::

    If you call `Sanic.get_app("non-existing")` on an app that does not exist, it will raise :class:`sanic.exceptions.SanicException` by default. You can, instead, force the method to return a new instance of Sanic with that name.

.. column::

    ```python
    app = Sanic.get_app(
        "non-existing",
        force_create=True,
    )
    ```


.. column::

    If there is **only one** Sanic instance registered, then calling `Sanic.get_app()` with no arguments will return that instance

.. column::

    ```python
    Sanic("My only app")

    app = Sanic.get_app()
    ```

## Configuration

.. column::

    Sanic holds the configuration in the `config` attribute of the `Sanic` instance. Configuration can be modified **either** using dot-notation **OR** like a dictionary.

.. column::

    ```python
    app = Sanic('myapp')

    app.config.DB_NAME = 'appdb'
    app.config['DB_USER'] = 'appuser'

    db_settings = {
        'DB_HOST': 'localhost',
        'DB_NAME': 'appdb',
        'DB_USER': 'appuser'
    }
    app.config.update(db_settings)
    ```



.. note:: Heads up

    Config keys _should_ be uppercase. But, this is mainly by convention, and lowercase will work most of the time.
    ```python
    app.config.GOOD = "yay!"
    app.config.bad = "boo"
    ```


There is much [more detail about configuration](../running/configuration.md) later on.

## Factory pattern

Many of the examples in these docs will show the instantiation of the :class:`sanic.app.Sanic` instance in a file called `server.py` in the "global scope" (i.e. not inside a function). This is a common pattern for very simple "hello world" style applications, but it is often beneficial to use a factory pattern instead.

A "factory" is just a function that returns an instance of the object you want to use. This allows you to abstract the instantiation of the object, but also may make it easier to isolate the application instance.

.. column::

    A super simple factory pattern could look like this:
    
.. column::

    ```python
    # ./path/to/server.py
    from sanic import Sanic
    from .path.to.config import MyConfig
    from .path.to.some.blueprint import bp
    
    
    def create_app(config=MyConfig) -> Sanic:
        app = Sanic("MyApp", config=config)
        app.blueprint(bp)
        return app
    ```

.. column::

    When we get to running Sanic later, you will learn that the Sanic CLI can detect this pattern and use it to run your application.
    
.. column::

    ```sh
    sanic path.to.server:create_app
    ```

## Customization

The Sanic application instance can be customized for your application needs in a variety of ways at instantiation.

For complete details, see the [API docs](/api/sanic.app).

### Custom configuration

.. column::

    This simplest form of custom configuration would be to pass your own object directly into that Sanic application instance

    If you create a custom configuration object, it is *highly* recommended that you subclass the :class:`sanic.config.Config` option to inherit its behavior. You could use this option for adding properties, or your own set of custom logic.

    *Added in v21.6*

.. column::

    ```python
    from sanic.config import Config

    class MyConfig(Config):
        FOO = "bar"

    app = Sanic(..., config=MyConfig())
    ```


.. column::

    A useful example of this feature would be if you wanted to use a config file in a form that differs from what is [supported](../running/configuration.md#using-sanicupdateconfig).

.. column::

    ```python
    from sanic import Sanic, text
    from sanic.config import Config

    class TomlConfig(Config):
        def __init__(self, *args, path: str, **kwargs):
            super().__init__(*args, **kwargs)

            with open(path, "r") as f:
                self.apply(toml.load(f))

        def apply(self, config):
            self.update(self._to_uppercase(config))

        def _to_uppercase(self, obj: Dict[str, Any]) -> Dict[str, Any]:
            retval: Dict[str, Any] = {}
            for key, value in obj.items():
                upper_key = key.upper()
                if isinstance(value, list):
                    retval[upper_key] = [
                        self._to_uppercase(item) for item in value
                    ]
                elif isinstance(value, dict):
                    retval[upper_key] = self._to_uppercase(value)
                else:
                    retval[upper_key] = value
            return retval

    toml_config = TomlConfig(path="/path/to/config.toml")
    app = Sanic(toml_config.APP_NAME, config=toml_config)
    ```

### Custom context

.. column::

    By default, the application context is a [`SimpleNamespace()`](https://docs.python.org/3/library/types.html#types.SimpleNamespace) that allows you to set any properties you want on it. However, you also have the option of passing any object whatsoever instead.

    *Added in v21.6*

.. column::

    ```python
    app = Sanic(..., ctx=1)
    ```

    ```python
    app = Sanic(..., ctx={})
    ```

    ```python
    class MyContext:
        ...

    app = Sanic(..., ctx=MyContext())
    ```

### Custom requests

.. column::

    It is sometimes helpful to have your own `Request` class, and tell Sanic to use that instead of the default. One example is if you wanted to modify the default `request.id` generator.

    

    .. note:: Important

        It is important to remember that you are passing the *class* not an instance of the class.


.. column::

    ```python
    import time

    from sanic import Request, Sanic, text

    class NanoSecondRequest(Request):
        @classmethod
        def generate_id(*_):
            return time.time_ns()

    app = Sanic(..., request_class=NanoSecondRequest)

    @app.get("/")
    async def handler(request):
        return text(str(request.id))
    ```

### Custom error handler

.. column::

    See [exception handling](../best-practices/exceptions.md#custom-error-handling) for more

.. column::

    ```python
    from sanic.handlers import ErrorHandler

    class CustomErrorHandler(ErrorHandler):
        def default(self, request, exception):
            ''' handles errors that have no error handlers assigned '''
            # You custom error handling logic...
            return super().default(request, exception)

    app = Sanic(..., error_handler=CustomErrorHandler())
    ```

### Custom dumps function

.. column::

    It may sometimes be necessary or desirable to provide a custom function that serializes an object to JSON data.

.. column::

    ```python
    import ujson

    dumps = partial(ujson.dumps, escape_forward_slashes=False)
    app = Sanic(__name__, dumps=dumps)
    ```


.. column::

    Or, perhaps use another library or create your own.

.. column::

    ```python
    from orjson import dumps

    app = Sanic("MyApp", dumps=dumps)
    ```

### Custom loads function

.. column::

    Similar to `dumps`, you can also provide a custom function for deserializing data.

    *Added in v22.9*

.. column::

    ```python
    from orjson import loads

    app = Sanic("MyApp", loads=loads)
    ```



.. new:: NEW in v23.6

    ### Custom typed application

Beginnint in v23.6, the correct type annotation of a default Sanic application instance is:

```python
sanic.app.Sanic[sanic.config.Config, types.SimpleNamespace]
```

It refers to two generic types:

1. The first is the type of the configuration object. It defaults to :class:`sanic.config.Config`, but can be any subclass of that.
2. The second is the type of the application context. It defaults to [`SimpleNamespace()`](https://docs.python.org/3/library/types.html#types.SimpleNamespace), but can be **any object** as show above.

Let's look at some examples of how the type will change.

.. column::

    Consider this example where we pass a custom subclass of :class:`sanic.config.Config` and a custom context object.

.. column::

    ```python
    from sanic import Sanic
    from sanic.config import Config

    class CustomConfig(Config):
        pass

    app = Sanic("test", config=CustomConfig())
    reveal_type(app) # N: Revealed type is "sanic.app.Sanic[main.CustomConfig, types.SimpleNamespace]"
    ```
    ```
    sanic.app.Sanic[main.CustomConfig, types.SimpleNamespace]
    ```


.. column::

    Similarly, when passing a custom context object, the type will change to reflect that.

.. column::

    ```python
    from sanic import Sanic

    class Foo:
        pass

    app = Sanic("test", ctx=Foo())
    reveal_type(app)  # N: Revealed type is "sanic.app.Sanic[sanic.config.Config, main.Foo]"
    ```
    ```
    sanic.app.Sanic[sanic.config.Config, main.Foo]
    ```


.. column::

    Of course, you can set both the config and context to custom types.

.. column::

    ```python
    from sanic import Sanic
    from sanic.config import Config

    class CustomConfig(Config):
        pass

    class Foo:
        pass

    app = Sanic("test", config=CustomConfig(), ctx=Foo())
    reveal_type(app)  # N: Revealed type is "sanic.app.Sanic[main.CustomConfig, main.Foo]"
    ```
    ```
    sanic.app.Sanic[main.CustomConfig, main.Foo]
    ```

This pattern is particularly useful if you create a custom type alias for your application instance so that you can use it to annotate listeners and handlers.

```python
# ./path/to/types.py
from sanic.app import Sanic
from sanic.config import Config
from myapp.context import MyContext
from typing import TypeAlias

MyApp = TypeAlias("MyApp", Sanic[Config, MyContext])
```

```python
# ./path/to/listeners.py
from myapp.types import MyApp

def add_listeners(app: MyApp):
    @app.before_server_start
    async def before_server_start(app: MyApp):
        # do something with your fully typed app instance
        await app.ctx.db.connect()
```

```python
# ./path/to/server.py
from myapp.types import MyApp
from myapp.context import MyContext
from myapp.config import MyConfig
from myapp.listeners import add_listeners

app = Sanic("myapp", config=MyConfig(), ctx=MyContext())
add_listeners(app)
```

*Added in v23.6*

.. new:: NEW in v23.6

    ### Custom typed request

Sanic also allows you to customize the type of the request object. This is useful if you want to add custom properties to the request object, or be able to access your custom properties of a typed application instance.

The correct, default type of a Sanic request instance is:

```python
sanic.request.Request[
    sanic.app.Sanic[sanic.config.Config, types.SimpleNamespace],
    types.SimpleNamespace
]
```

It refers to two generic types:

1. The first is the type of the application instance. It defaults to `sanic.app.Sanic[sanic.config.Config, types.SimpleNamespace]`, but can be any subclass of that.
2. The second is the type of the request context. It defaults to `types.SimpleNamespace`, but can be **any object** as show above in [custom requests](#custom-requests).

Let's look at some examples of how the type will change.

.. column::

    Expanding upon the full example above where there is a type alias for a customized application instance, we can also create a custom request type so that we can access those same type annotations.

    Of course, you do not need type aliases for this to work. We are only showing them here to cut down on the amount of code shown.

.. column::

    ```python
    from sanic import Request
    from myapp.types import MyApp
    from types import SimpleNamespace

    def add_routes(app: MyApp):
        @app.get("/")
        async def handler(request: Request[MyApp, SimpleNamespace]):
            # do something with your fully typed app instance
            results = await request.app.ctx.db.query("SELECT * FROM foo")
    ```


.. column::

    Perhaps you have a custom request object that generates a custom context object. You can type annotate it to properly access those properties with your IDE as shown here.

.. column::

    ```python
    from sanic import Request, Sanic
    from sanic.config import Config

    class CustomConfig(Config):
        pass

    class Foo:
        pass

    class RequestContext:
        foo: Foo

    class CustomRequest(Request[Sanic[CustomConfig, Foo], RequestContext]):
        @staticmethod
        def make_context() -> RequestContext:
            ctx = RequestContext()
            ctx.foo = Foo()
            return ctx

    app = Sanic(
        "test", config=CustomConfig(), ctx=Foo(), request_class=CustomRequest
    )

    @app.get("/")
    async def handler(request: CustomRequest):
        # Full access to typed:
        # - custom application configuration object
        # - custom application context object
        # - custom request context object
        pass
    ```

See more information in the [custom request context](./request#custom-request-context) section.

*Added in v23.6*

