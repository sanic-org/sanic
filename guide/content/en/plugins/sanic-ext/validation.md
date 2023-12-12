---
title: Sanic Extensions - Validation
---

# Validation

One of the most commonly implemented features of a web application is user-input validation. For obvious reasons, this is not only a security issue, but also just plain good practice. You want to make sure your data conforms to expectations, and throw a `400` response when it does not.

## Implementation

### Validation with Dataclasses

With the introduction of [Data Classes](https://docs.python.org/3/library/dataclasses.html), Python made it super simple to create objects that meet a defined schema. However, the standard library only supports type checking validation, **not** runtime validation. Sanic Extensions adds the ability to do runtime validations on incoming requests using `dataclasses` out of the box. If you also have either `pydantic` or `attrs` installed, you can alternatively use one of those libraries.

.. column::

    First, define a model.

.. column::

    ```python
    @dataclass
    class SearchParams:
        q: str
    ```


.. column::

    Then, attach it to your route

.. column::

    ```python
    from sanic_ext import validate

    @app.route("/search")
    @validate(query=SearchParams)
    async def handler(request, query: SearchParams):
        return json(asdict(query))
    ```


.. column::

    You should now have validation on the incoming request.

.. column::

    ```
    $ curl localhost:8000/search                                       
    ⚠️ 400 — Bad Request
    ====================
    Invalid request body: SearchParams. Error: missing a required argument: 'q'
    ```
    ```
    $ curl localhost:8000/search\?q=python                             
    {"q":"python"}
    ```

### Validation with Pydantic

You can use Pydantic models also.

.. column::

    First, define a model.

.. column::

    ```python
    class Person(BaseModel):
        name: str
        age: int
    ```


.. column::

    Then, attach it to your route

.. column::

    ```python
    from sanic_ext import validate

    @app.post("/person")
    @validate(json=Person)
    async def handler(request, body: Person):
        return json(body.dict())
    ```


.. column::

    You should now have validation on the incoming request.

.. column::

    ```
    $ curl localhost:8000/person -d '{"name": "Alice", "age": 21}' -X POST  
    {"name":"Alice","age":21}
    ```

### Validation with Attrs

You can use Attrs also.

.. column::

    First, define a model.

.. column::

    ```python
    @attrs.define
    class Person:
        name: str
        age: int

    ```


.. column::

    Then, attach it to your route

.. column::

    ```python
    from sanic_ext import validate

    @app.post("/person")
    @validate(json=Person)
    async def handler(request, body: Person):
        return json(attrs.asdict(body))
    ```


.. column::

    You should now have validation on the incoming request.

.. column::

    ```
    $ curl localhost:8000/person -d '{"name": "Alice", "age": 21}' -X POST  
    {"name":"Alice","age":21}
    ```

## What can be validated?

The `validate` decorator can be used to validate incoming user data from three places: JSON body data (`request.json`), form body data (`request.form`), and query parameters (`request.args`).

.. column::

    As you might expect, you can attach your model using the keyword arguments of the decorator.

.. column::

    ```python
    @validate(
        json=ModelA,
        query=ModelB,
        form=ModelC,
    )
    ```

