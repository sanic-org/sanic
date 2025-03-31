---
title: 无声扩展 - 基本OAS
---

# 基础知识

.. 注：

```
在 Sanic 扩展中实现OpenAPI 是基于从 [`sanic-openapi` ](https://github.com/sanic-org/sanic-openapi )实现的 OAS3 实现。 事实上，Sanic扩展在很大程度上是该项目的继承者，该项目在释放Sanic扩展后进入了维护模式。 如果你先前使用 `sanic-openapi` 的 OAS3 ，你应该有一个简单的路径升级到 Sanic Extensions. 不幸的是，该项目支持 OAS2 的规格。
```

.. 列:

```
在方框中，Sanic 扩展使用[v3.0 OpenAPI 规范](https://swagger.io/specification/)自动生成的 API 文档。您不需要做任何特殊操作
```

.. 列:

````
```python
from sanic import Sanic

app = Sanic("MyApp")

# 添加您所有的观点
```
````

在这么做之后，您现在将根据您现有的应用程序为您生成美丽的文档：

- [http://localhost:8000/docs](http://localhost:8000/docs)
- [http://localhost:8000/docs/redoc](http://localhost:8000/docs/redoc)
- [http://localhost:8000/docs/swagger](http://localhost:8000/docs/swagger)

签出[配置部分](../configuration.md) 以了解如何更改文档的路由。 您也可以关闭两个界面中的一个，并自定义界面，在`/docs`路由上可用。

.. 列:

```
使用 [Redoc](https://github.com/Redocly/Redoc)

！[Redoc](/assets/images/sanic-ext-redoc.png)
```

.. 列:

```
或 [Swagger UI](https://github.com/swagger-api/swagger-ui)

![Swagger UI](/assets/images/sanic-ext-swagger.png)
```

## 更改规范元数据

.. 列:

```
如果你想要更改任何元数据, 你应该使用 "描述" 方法。

在这个示例中使用 `edent` 和 `description` 参数来使多行字符串变得更加清洁。 这是不必要的，您可以在此传递任何字符串值。
```

.. 列:

````
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
````

