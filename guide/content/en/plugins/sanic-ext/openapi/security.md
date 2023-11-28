# Security Schemes

To document authentication schemes, there are two steps.

_Security is only available starting in v21.12.2_

## Document the scheme

.. column::

    The first thing that you need to do is define one or more security schemes. The basic pattern will be to define it as:

    ```python
    add_security_scheme("<NAME>", "<TYPE>")
    ```

    The `type` should correspond to one of the allowed security schemes: `"apiKey"`, `"http"`, `"oauth2"`, `"openIdConnect"`. You can then pass appropriate keyword arguments as allowed by the specification.

    You should consult the [OpenAPI Specification](https://swagger.io/specification/) for details on what values are appropriate.

.. column::

    ```python
    app.ext.openapi.add_security_scheme("api_key", "apiKey")
    app.ext.openapi.add_security_scheme(
        "token",
        "http",
        scheme="bearer",
        bearer_format="JWT",
    )
    app.ext.openapi.add_security_scheme("token2", "http")
    app.ext.openapi.add_security_scheme(
        "oldschool",
        "http",
        scheme="basic",
    )
    app.ext.openapi.add_security_scheme(
        "oa2",
        "oauth2",
        flows={
            "implicit": {
                "authorizationUrl": "http://example.com/auth",
                "scopes": {
                    "on:two": "something",
                    "three:four": "something else",
                    "threefour": "something else...",
                },
            }
        },
    )
    ```

## Document the endpoints

.. column::

    There are two options, document _all_ endpoints.

.. column::

    ```python
    app.ext.openapi.secured()
    app.ext.openapi.secured("token")
    ```


.. column::

    Or, document only specific routes.

.. column::

    ```python
    @app.route("/one")
    async def handler1(request):
        """
        openapi:
        ---
        security:
            - foo: []
        """

    @app.route("/two")
    @openapi.secured("foo")
    @openapi.secured({"bar": []})
    @openapi.secured(baz=[])
    async def handler2(request):
        ...

    @app.route("/three")
    @openapi.definition(secured="foo")
    @openapi.definition(secured={"bar": []})
    async def handler3(request):
        ...
    ```

