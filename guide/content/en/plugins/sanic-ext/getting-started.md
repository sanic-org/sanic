---
title: Sanic Extensions - Getting Started
---

# Getting Started

Sanic Extensions is an *officially supported* plugin developed, and maintained by the SCO. The primary goal of this project is to add additional features to help Web API and Web application development easier.

## Features

- CORS protection
- Template rendering with Jinja
- Dependency injection into route handlers
- OpenAPI documentation with Redoc and/or Swagger
- Predefined, endpoint-specific response serializers
- Request query arguments and body input validation
- Auto create `HEAD`, `OPTIONS`, and `TRACE` endpoints

## Minimum requirements

- **Python**: 3.8+
- **Sanic**: 21.9+

## Install

The best method is to just install Sanic Extensions along with Sanic itself:

```bash
pip install sanic[ext]
```

You can of course also just install it by itself.

```bash
pip install sanic-ext
```

## Extend your application

Out of the box, Sanic Extensions will enable a bunch of features for you. 

.. column::

    To setup Sanic Extensions (v21.12+), you need to do: **nothing**. If it is installed in the environment, it is setup and ready to go.

    This code is the Hello, world app in the [Sanic Getting Started page](../../guide/getting-started.md) _without any changes_, but using Sanic Extensions with `sanic-ext` installed in the background.

.. column::

    ```python
    from sanic import Sanic
    from sanic.response import text

    app = Sanic("MyHelloWorldApp")

    @app.get("/")
    async def hello_world(request):
        return text("Hello, world.")
    ```


.. column::

    **_OLD DEPRECATED SETUP_**

    In v21.9, the easiest way to get started is to instantiate it with `Extend`.

    If you look back at the Hello, world app in the [Sanic Getting Started page](../../guide/getting-started.md), you will see the only additions here are the two highlighted lines.

.. column::

    ```python
    from sanic import Sanic
    from sanic.response import text
    from sanic_ext import Extend

    app = Sanic("MyHelloWorldApp")
    Extend(app)

    @app.get("/")
    async def hello_world(request):
        return text("Hello, world.")
    ```

Regardless of how it is setup, you should now be able to view the OpenAPI documentation and see some of the functionality in action: [http://localhost:8000/docs](http://localhost:8000/docs).
