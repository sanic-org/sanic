# Decorators

The primary mechanism for adding content to your schema is by decorating your endpoints. If you have
used `sanic-openapi` in the past, this should be familiar to you. The decorators and their arguments match closely
the [OAS v3.0 specification](https://swagger.io/specification/).

.. column::

    All of the examples show will wrap around a route definition. When you are creating these, you should make sure that
    your Sanic route decorator (`@app.route`, `@app.get`, etc) is the outermost decorator. That is to say that you should
    put that first and then one or more of the below decorators after.

.. column::

    ```python
    from sanic_ext import openapi

    @app.get("/path/to/<something>")
    @openapi.summary("This is a summary")
    @openapi.description("This is a description")
    async def handler(request, something: str):
        ...
    ```


.. column::

    You will also see a lot of the below examples reference a model object. For the sake of simplicity, the examples will
    use `UserProfile` that will look like this. The point is that it can be any well-typed class. You could easily imagine
    this being a `dataclass` or some other kind of model object.

.. column::

    ```python
    class UserProfile:
        name: str
        age: int
        email: str
    ```

## Definition decorator

### `@openapi.definition`

The `@openapi.definition` decorator allows you to define all parts of an operations on a path at once. It is an omnibums
decorator in that it has the same capabilities to create operation definitions as the rest of the decorators. Using
multiple field-specific decorators or a single decorator is a style choice for you the developer.

The fields are purposely permissive in accepting multiple types to make it easiest for you to define your operation.

**Arguments**

| Field         | Type                                                                      |
| ------------- | --------------------------------------------------------------------------|
| `body`        | **dict, RequestBody, *YourModel***                                        |
| `deprecated`  | **bool**                                                                  |
| `description` | **str**                                                                   |
| `document`    | **str, ExternalDocumentation**                                            | 
| `exclude`     | **bool**                                                                  |
| `operation`   | **str**                                                                   |
| `parameter`   | **str, dict, Parameter, [str], [dict], [Parameter]**                      |
| `response`    | **dict, Response, *YourModel*, [dict], [Response]**                       |
| `summary`     | **str**                                                                   |
| `tag`         | **str, Tag, [str], [Tag]**                                                |
| `secured`     | **Dict[str, Any]**                                                        |

**Examples**

.. column::

    ```python
    @openapi.definition(
        body=RequestBody(UserProfile, required=True),
        summary="User profile update",
        tag="one",
        response=[Success, Response(Failure, status=400)],
    )
    ```

.. column::



*See below examples for more examples. Any of the values for the below decorators can be used in the corresponding
keyword argument.*

## Field-specific decorators

All the following decorators are based on `@openapi`

:

.. tabs:: :::tab body

    **Arguments**

    | Field       | Type                               |
    | ----------- | ---------------------------------- |
    | **content** | ***YourModel*, dict, RequestBody** |

    **Examples**

    .. column::

        ```python
        @openapi.body(UserProfile)
        ```

        ```python
        @openapi.body({"application/json": UserProfile})
        ```

        ```python
        @openapi.body(RequestBody({"application/json": UserProfile}))
        ```

    .. column::

        ```python
        @openapi.body({"content": UserProfile})
        ```

        ```python
        @openapi.body(RequestBody(UserProfile))
        ```

        ```python
        @openapi.body({"application/json": {"description": ...}})
        ```



.. tab:: deprecated

    **Arguments**

    *None*

    **Examples**

    .. column::

        ```python
        @openapi.deprecated()
        ```

    .. column::

        ```python
        @openapi.deprecated
        ```



.. tab:: description

    **Arguments**

    | Field  | Type    |
    | ------ | ------- |
    | `text` | **str** |

    **Examples**

    .. column::

        ```python
        @openapi.description(
            """This is a **description**.

        ## You can use `markdown`

        - And
        - make
        - lists.
        """
        )
        ```

    .. column::



.. tab:: document

    **Arguments**

    | Field         | Type    |
    | ------------- | ------- |
    | `url`         | **str** |
    | `description` | **str** |

    **Examples**

    .. column::

        ```python
        @openapi.document("http://example.com/docs")
        ```

    .. column::

        ```python
        @openapi.document(ExternalDocumentation("http://example.com/more"))
        ```



.. tab:: exclude

    Can be used on route definitions like all of the other decorators, or can be called on a Blueprint

    **Arguments**

    | Field  | Type          | Default  |
    | ------ | ------------- | -------- |
    | `flag` | **bool**      | **True** |
    | `bp`   | **Blueprint** |          |

    **Examples**

    .. column::

        ```python
        @openapi.exclude()
        ```

    .. column::

        ```python
        openapi.exclude(bp=some_blueprint)
        ```



.. tab:: operation

    Sets the operation ID.

    **Arguments**

    | Field  | Type    |
    | ------ | ------- |
    | `name` | **str** |

    **Examples**

    .. column::

        ```python
        @openapi.operation("doNothing")
        ```

    .. column::



.. tab:: parameter

    **Arguments**

    | Field      | Type                                      | Default     |
    | ---------- | ----------------------------------------- | ----------- |
    | `name`     | **str**                                   |             |
    | `schema`   | ***type***                                | **str**     |
    | `location` | **"query", "header", "path" or "cookie"** | **"query"** |

    **Examples**

    .. column::

        ```python
        @openapi.parameter("thing")
        ```

        ```python
        @openapi.parameter(parameter=Parameter("foobar", deprecated=True))
        ```

    .. column::

        ```python
        @openapi.parameter("Authorization", str, "header")
        ```

        ```python
        @openapi.parameter("thing", required=True, allowEmptyValue=False)
        ```



.. tab:: response

    **Arguments**

    If using a `Response` object, you should not pass any other arguments.

    | Field         | Type                          |
    | ------------- | ----------------------------- |
    | `status`      | **int**                       |
    | `content`     | ***type*, *YourModel*, dict** |
    | `description` | **str**                       |
    | `response`    | **Response**                  |

    **Examples**

    .. column::

        ```python
        @openapi.response(200, str, "This is endpoint returns a string")
        ```

        ```python
        @openapi.response(200, {"text/plain": str}, "...")
        ```

        ```python
        @openapi.response(response=Response(UserProfile, description="..."))
        ```

        ```python
        @openapi.response(
            response=Response(
                {
                    "application/json": UserProfile,
                },
                description="...",
                status=201,
            )
        )
        ```

    .. column::

        ```python
        @openapi.response(200, UserProfile, "...")
        ```

        ```python
        @openapi.response(
            200,
            {
                "application/json": UserProfile,
            },
            "Description...",
        )
        ```



.. tab:: summary

    **Arguments**

    | Field  | Type    |
    | ------ | ------- |
    | `text` | **str** |

    **Examples**

    .. column::

        ```python
        @openapi.summary("This is an endpoint")
        ```

    .. column::



.. tab:: tag

    **Arguments**

    | Field   | Type         |
    | ------- | ------------ |
    | `*args` | **str, Tag** |

    **Examples**

    .. column::

        ```python
        @openapi.tag("foo")
        ```

    .. column::

        ```python
        @openapi.tag("foo", Tag("bar"))
        ```



.. tab:: secured

    **Arguments**

    | Field             | Type                    |
    | ----------------- | ----------------------- |
    | `*args, **kwargs` | **str, Dict[str, Any]** |

    **Examples**

    .. column::

        ```python
        @openapi.secured()
        ```

    .. column::



    .. column::

        ```python
        @openapi.secured("foo")
        ```

    .. column::

        ```python
        @openapi.secured("token1", "token2")
        ```


    .. column::

        ```python
        @openapi.secured({"my_api_key": []})
        ```

    .. column::

        ```python
        @openapi.secured(my_api_key=[])
        ```

    Do not forget to use `add_security_scheme`. See [security](./security.md) for more details.


::::

## Integration with Pydantic

Pydantic models have the ability to [generate OpenAPI schema](https://pydantic-docs.helpmanual.io/usage/schema/). 

.. column::

    To take advantage of Pydantic model schema generation, pass the output in place of the schema.

.. column::

    ```python
    from sanic import Sanic, json
    from sanic_ext import validate, openapi
    from pydantic import BaseModel, Field

    class Test(BaseModel):
        foo: str = Field(description="Foo Description", example="FOOO")
        bar: str = "test"

    app = Sanic("test")

    @app.get("/")
    @openapi.definition(
        body={'application/json': Test.schema()},
    )
    @validate(json=Test)
    async def get(request):
        return json({})
    ```

*Added in v22.9*
