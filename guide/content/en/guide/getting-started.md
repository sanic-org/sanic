# Getting Started

Before we begin, make sure you are running Python 3.9 or higher. Currently, Sanic is works with Python versions 3.9 – 3.13.

## Install

```sh
pip install sanic
```

## Hello, world application

.. column::

    If you have ever used one of the many decorator based frameworks, this probably looks somewhat familiar to you.

    

    .. note:: 

        If you are coming from Flask or another framework, there are a few important things to point out. Remember, Sanic aims for performance, flexibility, and ease of use. These guiding principles have tangible impact on the API and how it works.

.. column::

    ```python
    from sanic import Sanic
    from sanic.response import text

    app = Sanic("MyHelloWorldApp")

    @app.get("/")
    async def hello_world(request):
        return text("Hello, world.")
    ```

### Important to note

- Every request handler can either be sync (`def hello_world`) or async (`async def hello_world`). Unless you have a clear reason for it, always go with `async`.
- The `request` object is always the first argument of your handler. Other frameworks pass this around in a context variable to be imported. In the `async` world, this would not work so well and it is far easier (not to mention cleaner and more performant) to be explicit about it. 
- You **must** use a response type. MANY other frameworks allow you to have a return value like this: `return "Hello, world."` or this: `return {"foo": "bar"}`. But, in order to do this implicit calling, somewhere in the chain needs to spend valuable time trying to determine what you meant. So, at the expense of this ease, Sanic has decided to require an explicit call.

### Running

.. column::

    Let's save the above file as `server.py`. And launch it.

.. column::

    ```sh
    sanic server
    ```

.. note:: 

    This **another** important distinction. Other frameworks come with a built in development server and explicitly say that it is _only_ intended for development use. The opposite is true with Sanic. 

    **The packaged server is production ready.**


## Sanic Extensions

Sanic intentionally aims for a clean and unopinionated feature list. The project does not want to require you to build your application in a certain way, and tries to avoid prescribing specific development patterns. There are a number of third-party plugins that are built and maintained by the community to add additional features that do not otherwise meet the requirements of the core repository.

However, in order **to help API developers**, the Sanic organization maintains an official plugin called [Sanic Extensions](../plugins/sanic-ext/getting-started.md) to provide all sorts of goodies, including:

- **OpenAPI** documentation with Redoc and/or Swagger
- **CORS** protection
- **Dependency injection** into route handlers
- Request query arguments and body input **validation**
- Auto create `HEAD`, `OPTIONS`, and `TRACE` endpoints
- Predefined, endpoint-specific response serializers

The preferred method to set it up is to install it along with Sanic, but you can also install the packages on their own.

.. column::

    ```sh
    pip install sanic[ext]
    ```

.. column::

    ```sh
    pip install sanic sanic-ext
    ```

Starting in v21.12, Sanic will automatically setup Sanic Extensions if it is in the same environment. You will also have access to two additional application properties:

- `app.extend()` - used to configure Sanic Extensions
- `app.ext` - the `Extend` instance attached to the application

See [the plugin documentation](../plugins/sanic-ext/getting-started.md) for more information about how to use and work with the plugin
