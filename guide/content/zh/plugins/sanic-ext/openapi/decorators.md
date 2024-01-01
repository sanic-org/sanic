---
title: 无声扩展 - 美洲组织装饰师
---

# 装饰符

将内容添加到您的方案的主要机制是通过装饰您的终点。 If you have
used `sanic-openapi` in the past, this should be familiar to you. 装饰者及其参数与[OAS v3.0 规格](https://swagger.io/specialization/)密切匹配
。

.. 列:

```
All of the examples show will wrap around a route definition. When you are creating these, you should make sure that
your Sanic route decorator (`@app.route`, `@app.get`, etc) is the outermost decorator. That is to say that you should
put that first and then one or more of the below decorators after.
```

.. 列:

````
```python
来自sanic_ext importing openapi

@app.get("/path/to/<something>")
@openapi.summary("这是一个摘要")
@openapi。 escription("这是一个描述")
async def 处理器(请求, 内容: str):
    ...
```
````

.. 列:

```
您还将看到许多下面的示例引用模型对象。 为了简洁起见，示例将为
使用 'UserProfile` 。 问题是，它可以是任何类型良好的类。 您可以轻松地想象一下
这是一个 `dataclass` 或某种其他类型的模型对象。
```

.. 列:

````
```python
class UserProfile:
    name: str
    age: int
    email: str
```
````

## 定义装饰符

### `@openapi.definition`

`@openapi.definition`装饰器允许您同时在路径上定义操作的所有部分。 它是一个
装饰器，它具有与其他装饰者相同的创建操作定义的能力。 使用
多个特定字段的装饰符或单个装饰符是你开发者的样式选择。

字段有意允许接受多种类型，使您最容易定义您的操作。

**参数**

| 字段          | 类型                                                                                                                                                                                                        |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `body`      | **dict, RequestBody, _YourModel_**                                                                                                                                                                        |
| `已弃用`       | **布尔**                                                                                                                                                                                                    |
| `描述`        | **str**                                                                                                                                                                                                   |
| `文档`        | **str, ExternalDocumentation**                                                                                                                                                                            |
| `exclude`   | **布尔**                                                                                                                                                                                                    |
| `operation` | **str**                                                                                                                                                                                                   |
| `参数`        | **str, dict, 参数, [str], [dict], [Parameter]** |
| `response`  | **dict, Response, _YourModel_, [dict], [Response]**                                               |
| `summary`   | **str**                                                                                                                                                                                                   |
| `tag`       | **str, Tag, [str], [Tag]**                                                                        |
| `securd`    | **Dict[str, Any]**                                                                                                                                    |

**示例**

.. 列:

````
```python
@openapi.definition(
    body=RequestBody(UserProfile, required=True),
    summary="User profile",
    tag="one",
    response=[Success, ResponseFailure, status=400)],
)
```
````

.. 列:

- 更多例子见下文。 以下装饰符的任何值都可以在对应的
  关键字参数中使用。\*

## 场地特定装饰

以下所有装饰符都基于 `@openapi`

### 正文内容

**参数**

| 字段     | 类型                                 |
| ------ | ---------------------------------- |
| **内容** | **_YourModel_, dict, RequestBody** |

**示例**

.. 列:

````
```python
@openapi.body(UserProfile)
```

``python
@openapi.body({"application/json": UserProfile})
```

```python
@openapi.body(RequestBody({"application/json": UserProfile}))
```
````

.. 列:

````
```python
@openapi.body({"content": UserProfile})
```

```python
@openapi.body(RequestBody(UserProfile))
```

```python
@openapi.body({"application/json": {"description": ...}})
```
````

### 已弃用

**参数**

_无_

**示例**

.. 列:

````
```python
@openapi.过时()
```
````

.. 列:

````
```python
@openapi.废弃的
```
````

### 描述

**参数**

| 字段     | 类型      |
| ------ | ------- |
| `text` | **str** |

**示例**

.. 列:

````
```python
@openapi.description(
    """这是一个**描述** 。

## 你可以使用 "markdown"

- 和
- make
- 列表。
"""
)
```
````

.. 列:

### 文档

**参数**

| 字段    | 类型      |
| ----- | ------- |
| `url` | **str** |
| `描述`  | **str** |

**示例**

.. 列:

````
```python
@openapi.document("http://example.com/docs")
```
````

.. 列:

````
```python
@openapi.document(ExternalDocumentation("http://example.com/more"))
```
````

### 不包含

可以像所有其他装饰器一样用于路由定义，或者可以在蓝图上调用

**参数**

| 字段     | 类型     | 默认设置     |
| ------ | ------ | -------- |
| `flag` | **布尔** | **True** |
| `bp`   | **蓝图** |          |

**示例**

.. 列:

````
```python
@openapi.exclude()
```
````

.. 列:

````
```python
openapi.exclude(bp=some_bluprint)
```
````

### 操作

设置操作 ID。

**参数**

| 字段     | 类型      |
| ------ | ------- |
| `name` | **str** |

**示例**

.. 列:

````
```python
@openapi.operation("doNothing")
```
````

.. 列:

**参数**

| 字段         | 类型                                    | 默认设置     |
| ---------- | ------------------------------------- | -------- |
| `name`     | **str**                               |          |
| `schema`   | _**type**_                            | **str**  |
| `location` | **"查询", "header", "path" 或 "cookie"** | **"查询"** |

**示例**

.. 列:

````
```python
@openapi.parameter("thing")
```

``python
@openapi.parameter(parameter=Parameter("foobar", 过时=True))
```
````

.. 列:

````
```python
@openapi.parameter("Authorization", str, "header")
```

``python
@openapi.parameter("thing", required=True, allowEmptyValue=False)
```
````

### 应答

**参数**

如果使用 "Response" 对象，您不应传递任何其他参数。

| 字段         | 类型                          |
| ---------- | --------------------------- |
| `status`   | **int**                     |
| `content`  | **_类型_, _YourModel_, dict** |
| `描述`       | **str**                     |
| `response` | **答复**                      |

**示例**

.. 列:

````
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
````

.. 列:

````
```python
@openapi.response200, UserProfile, "...")
```

```python
@openapi。 esponse(
    200,
    然后才能
        "application/json": UserProfile,
    },
    "描述. .",
)
```
````

### summary

**参数**

| 字段     | 类型      |
| ------ | ------- |
| `text` | **str** |

**示例**

.. 列:

````
```python
@openapi.summary("这是一个终点")

````

.. 列:

### 标签

**参数**

| 字段      | 类型           |
| ------- | ------------ |
| `*args` | **str, Tag** |

**示例**

.. 列:

````
```python
@openapi.tag("foo")
```
````

.. 列:

````
```python
@openapi.tag("foo", Tag("bar"))
```
````

### 安全的

**参数**

| 字段                | 类型                                                                          |
| ----------------- | --------------------------------------------------------------------------- |
| `*args, **kwargs` | **str, Dict[str, Any]** |

**示例**

.. 列:

````
```python
@openapi.secured()
```
````

.. 列:

.. 列:

````
```python
@openapi.secured("foo")
```
````

.. 列:

````
```python
@openapi.secured("token1", "token2")
```
````

.. 列:

````
```python
@openapi.secured({"my_api_key": []})
```
````

.. 列:

````
```python
@openapi.secured(my_api_key=[])
```
````

不要忘记使用 add_security_scheme\` 。 更多详细信息请访问 [security](./security.md)。
\`\`

## 与 Pydantic集成

Pydantic模型有能力[生成 OpenAPI 方案](https://pydantic-docs.helpmanual.io/usage/schema/)。

.. 列:

```
为了利用Pydantic模型架构生成，将输出转换为架构。
```

.. 列:

````
```python
from sanic import Sanic, json
from sanic_ext import validate, openapi
from pydantic import BaseModel, Field

@openapi.component
class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None

class ItemList(BaseModel):
    items: List[Item]

app = Sanic("test")

@app.get("/")
@openapi.definition(
    body={
        "application/json": ItemList.schema(
            ref_template="#/components/schemas/{model}"
        )
    },
)
async def get(request):
    return json({})
```
````

.. 注：

```
设置`ref_template`非常重要。默认情况下，Pydantic将选择一个非标准的 OAS模板。 这将导致在生成最后文档时找不到样式。
```

_添加于 v22.9_
