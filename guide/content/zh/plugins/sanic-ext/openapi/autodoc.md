---
title: Sanic 扩展 - 自动生成文档
---

# 自动文档

要使得创建API文档页面变得更容易，Sanic 扩展可以使用函数的 docstring 来自动化填充您的文档。

## 摘要和说明

.. 列:

```
函数的 docstring 将用于创建摘要和描述。 从这里的例子中你可以看到， docstring 已被解析成：第一行作为总结，字符串的其余部分作为描述。
```

.. 列:

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

## 操作级别的 YAML

.. 列:

```
你可以通过将有效的 OpenAPI YAML 添加到文档字符串来扩展这个。只需添加一行包含 `openapi:`, 然后是你的 YAML。 

示例中显示的 "---" 是*不需要*。 只是为了帮助视觉辨认YAML是文档的一个独特部分。
```

.. 列:

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

.. 注：

```
当使用YAML文档和装饰器时，在生成文档时优先考虑的是装饰器的内容。
```

## 不包括文档字符串

.. 列:

```
有时候函数可能包含一个文档字符串，该字符串不打算在文档内消耗。

**选项1**：全局关闭自动文档“应用”。 onfig.OAS_AUTODOC = False`

**选项2**：使用 `@openapi.no_autodoc` 装饰器禁用单个处理程序
```

.. 列:

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
