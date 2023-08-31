# Basics


.. note::

    The OpenAPI implementation in Sanic Extensions is based upon the OAS3 implementation from [`sanic-openapi`](https://github.com/sanic-org/sanic-openapi). In fact, Sanic Extensions is in a large way the successor to that project, which entered maintenance mode upon the release of Sanic Extensions. If you were previously using OAS3 with `sanic-openapi` you should have an easy path to upgrading to Sanic Extensions. Unfortunately, this project does *NOT* support the OAS2 specification.



.. column::

    Out of the box, Sanic Extensions provides automatically generated API documentation using the [v3.0 OpenAPI specification](https://swagger.io/specification/). There is nothing special that you need to do

.. column::

    ```python
    from sanic import Sanic

    app = Sanic("MyApp")

    # Add all of your views
    ```

After doing this, you will now have beautiful documentation already generated for you based upon your existing application:

- [http://localhost:8000/docs](http://localhost:8000/docs)
- [http://localhost:8000/docs/redoc](http://localhost:8000/docs/redoc)
- [http://localhost:8000/docs/swagger](http://localhost:8000/docs/swagger)

Checkout the [section on configuration](../configuration.md) to learn about changing the routes for the docs. You can also turn off one of the two UIs, and customize which UI will be available on the `/docs` route.

.. column::

    Using [Redoc](https://github.com/Redocly/redoc)

    ![Redoc](/assets/images/sanic-ext-redoc.png)

.. column::

    or [Swagger UI](https://github.com/swagger-api/swagger-ui)

    ![Swagger UI](/assets/images/sanic-ext-swagger.png)

## Changing specification metadata

.. column::

    If you want to change any of the metada, you should use the `describe` method.

    In this example `dedent` is being used with the `description` argument to make multi-line strings a little cleaner. This is not necessary, you can pass any string value here.

.. column::

    ```python
    from textwrap import dedent

    app.ext.openapi.describe(
        "Testing API",
        version="1.2.3",
        description=dedent(
            """
            # Info
            This is a description. It is a good place to add some _extra_ doccumentation.

            **MARKDOWN** is supported.
            """
        ),
    )
    ```

