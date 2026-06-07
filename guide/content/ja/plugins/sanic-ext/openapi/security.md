---
title: サニックエクステンション - OASセキュリティスキーム
---

# セキュリティスキーム

認証スキームを文書化するには、2つのステップがあります。

_Security は v21.12.2_ からのみ利用できます。

## スキームをドキュメント

.. 列::

````
The first thing that you need to do is define one or more security schemes. The basic pattern will be to define it as:

```python
add_security_scheme("<NAME>", "<TYPE>")
```

The `type` should correspond to one of the allowed security schemes: `"apiKey"`, `"http"`, `"oauth2"`, `"openIdConnect"`. You can then pass appropriate keyword arguments as allowed by the specification.

You should consult the [OpenAPI Specification](https://swagger.io/specification/) for details on what values are appropriate.
````

.. 列::

````
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
````

## エンドポイントをドキュメント

.. 列::

```
2つのオプションがあります。文書には_all_エンドポイントがあります。
```

.. 列::

````
```python
app.ext.openapi.secured()
app.ext.openapi.secured("token")
```
````

.. 列::

```
または、特定のルートのみをドキュメントします。
```

.. 列::

````
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
````

