---
title: 无声扩展——美洲国家组织的安全计划
---

# 安全方案

要记载认证计划，有两个步骤。

_Security 仅在 v21.12.2_ 开始

## 记录方案

.. 列:

````
您需要做的第一件事是定义一个或多个安全方案。 基本模式将定义为：

``python
add_security_scheme("<NAME>", "<TYPE>")
```

`type` 应该对应于允许的安全方案之一：`"apiKey", `"http", `oauth2", `"openIdConnect"。 然后您可以通过指定允许的适当关键字参数。

您应该咨询[OpenAPI Specification](https://swagger.io/specification/) 了解什么值是合适的。
````

.. 列:

````
```python
app.ext.openapi.add_security_scheme("api_key", "apiKey")
app.ext.openapi。 dd_security_scheme(
    "token",
    "http",
    scheme="bearer",
    bearer_form="JWT",
)
应用。 xt.openapi.add_security_scheme("token2", "http")
app.ext.openapi。 dd_security_scheme(
    "老学校",
    "http",
    scheme="basic",
)
app.ext.openapi。 dd_security_scheme(
    "oa2",
    "oauth2",
    flows=own
        "implicit": 哇，
            "authorizationUrl": "http://example"。 om/auth”，
            "scopes": Power
                "on:two": "something",
                "the:four ": "some other",
                "三": "其他东西. .",
            },
        }
    },
)
```
````

## 记录终点

.. 列:

```
有两个选项，文件 _all_endpoint。
```

.. 列:

````
```python
app.ext.openapi.secured()
app.ext.openapi.secured("token")
```
````

.. 列:

```
或者只文档特定的路由。
```

.. 列:

````
```python
@app。 oute("/one")
async def handler1(request):
    """
    openapi:
    -
    security:
        - foo: []
    ""”

@app. oute("/tw")
@openapi.secured("foo")
@openapi。 普遍({"bar"：[]})
@openapi.secured(baz=[])
async def 处理器2(请求)：
    ...

@app.route("/the")
@openapi。 finition(secured="foo")
@openapi.definition(secured={"bar": []})
async def handler3(request):
    ...
```
````
