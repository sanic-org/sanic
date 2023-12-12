---
title: Sanic Extensions - Auto-documentation
---

# Auto-documentation

To make documenting endpoints easier, Sanic Extensions will use a function's docstring to populate your documentation. 

## Summary and description

.. column::

    A function's docstring will be used to create the summary and description. As you can see from this example here, the docstring has been parsed to use the first line as the summary, and the remainder of the string as the description.

.. column::

    ```python
    @app.get("/foo")
    async def handler(request, something: str):
        """This is a simple foo handler

        It is helpful to know that you could also use **markdown** inside your
        docstrings.

        - one
        - two
        - three"""
        return text(">>>")
    ```
    ```json
    "paths": {
      "/foo": {
        "get": {
          "summary": "This is a simple foo handler",
          "description": "It is helpful to know that you could also use **markdown** inside your<br>docstrings.<br><br>- one<br>- two<br>- three",
          "responses": {
            "default": {
              "description": "OK"
            }
          },
          "operationId": "get_handler"
        }
      }
    }
    ```

## Operation level YAML

.. column::

    You can expand upon this by adding valid OpenAPI YAML to the docstring. Simply add a line that contains `openapi:`, followed by your YAML. 

    The `---` shown in the example is *not* necessary. It is just there to help visually identify the YAML as a distinct section of the docstring.

.. column::

    ```python
    @app.get("/foo")
    async def handler(request, something: str):
        """This is a simple foo handler

        Now we will add some more details

        openapi:
        ---
        operationId: fooDots
        tags:
          - one
          - two
        parameters:
          - name: limit
            in: query
            description: How many items to return at one time (max 100)
            required: false
            schema:
              type: integer
              format: int32
        responses:
          '200':
            description: Just some dots
        """
        return text("...")
    ```
    ```json
    "paths": {
      "/foo": {
        "get": {
          "operationId": "fooDots",
          "summary": "This is a simple foo handler",
          "description": "Now we will add some more details",
          "tags": [
            "one",
            "two"
          ],
          "parameters": [
            {
              "name": "limit",
              "in": "query",
              "description": "How many items to return at one time (max 100)",
              "required": false,
              "schema": {
                "type": "integer",
                "format": "int32"
              }
            }
          ],
          "responses": {
            "200": {
              "description": "Just some dots"
            }
          }
        }
      }
    }
    ```



.. note:: 

    When both YAML documentation and decorators are used, it is the content from the decorators that will take priority when generating the documentation.



## Excluding docstrings

.. column::

    Sometimes a function may contain a docstring that is not meant to be consumed inside the documentation.

    **Option 1**: Globally turn off auto-documentation `app.config.OAS_AUTODOC = False`

    **Option 2**: Disable it for the single handler with the `@openapi.no_autodoc` decorator

.. column::

    ```python
    @app.get("/foo")
    @openapi.no_autodoc
    async def handler(request, something: str):
        """This is a docstring about internal info only. Do not parse it.
        """
        return text("...")
    ```

