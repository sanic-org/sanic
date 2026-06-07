---
title: サニックエクステンション - 自動ドキュメント
---

# 自動ドキュメント

エンドポイントの文書化を容易にするために、Sanic Extensionsはdocstringを使ってドキュメントを作成します。

## 概要と説明

.. 列::

```
要約と説明を作成するために、関数の docstring が使用されます。 この例からわかるように、docstringは最初の行を要約として使用するようにパースされています。 文字列の説明として残りの部分を指定します。
```

.. 列::

````
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
````

## 操作レベルYAML

.. 列::

```
これを展開するには、有効なOpenAPI YAML を docstring に追加します。単純に `openapi:` を含む行を追加し、その後に YAML を追加します。 

例に示す`---`は*不要*です。 YAML をドキュメント文字列の明確なセクションとして視覚的に識別するために、そこにあるだけです。
```

.. 列::

````
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
````

.. note::

```
YAML ドキュメントとデコレータの両方が使用される場合、ドキュメントを生成する際に優先されるデコレータのコンテンツです。
```

## docstringsを除外

.. 列::

```
Sometimes a function may contain a docstring that is not meant to be consumed inside the documentation.

**Option 1**: Globally turn off auto-documentation `app.config.OAS_AUTODOC = False`

**Option 2**: Disable it for the single handler with the `@openapi.no_autodoc` decorator
```

.. 列::

````
```python
@app.get("/foo")
@openapi.no_autodoc
async def handler(request, something: str):
    """This is a docstring about internal info only. Do not parse it.
    """
    return text("...")
```
````

