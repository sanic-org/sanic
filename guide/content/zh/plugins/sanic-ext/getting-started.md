---
title: Sanic 扩展 - 开始使用
---

# 正在开始

Sanic 扩展是由 SCO开发和维护的 _官方支持_ 插件。 这个项目的主要目标是增加额外的功能，帮助Web API 和Web 应用程序开发更容易。

## 功能

- CORS 保护
- 使用 Jinja 渲染模板
- 依赖注入路由处理
- 与 Redoc 或 Swagger 的 OpenAPI 文档
- 预定义的端点特定响应序列转换器
- 请求查询参数和实体输入验证
- 自动创建 `HEAD`, `OPTIONS` 和 `TRACE` 终点

## 最低要求

- **Python**: 3.8+
- **Sanic**: 21.9+

## 安装

最好的方法是立即安装 Sanic 扩展以及Sanic 本身：

```bash
pip install sanic[ext]
```

当然你也可以自己安装它。

```bash
pip 安装 sanic-ext
```

## 扩展您的应用程序

Sanic 扩展将从箱子中为您启用一堆功能。

.. 列:

```
若要设置 Sanic 扩展 (v21.12+), 您需要做: **nithing** 。如果它是在环境中安装的，它将被设置并准备就绪。

此代码是Hello, 世界应用在 [Sanic Getting Started page](../../guide/getting-started). d) _没有任何更改_, 但使用 Sanic Extensions 使用 `sanic-ext` 在后台安装。
```

.. 列:

````
```python
from sanic importing Sanic
from sanic.response import text

app = Sanic("MyHelloWorldApp")

@app. et("/")
async def hello_world(request):
    return text("Hello, world.")
```
````

.. 列:

```
**_OLD DEPRECATED SETUP_**

在 v21.9中，最容易启动的方法是使用 `Extend` 实例化它。

如果你回到你好，世界应用在 [Sanic Getting Started页面](../) 向导/getting-started.md, 您将看到这里唯一的添加是两行高亮显示。
```

.. 列:

````
```python
from sanic import Sanic
from sanic.response import text
from sanic_ext import Extend

app = Sanic("MyHelloWorldApp")
Extend(app)

@app.get("/")
async def hello_world(request):
    return text("Hello, world.")
```
````

无论如何设置，您现在都应该能够查看 OpenAPI 文档，并查看一些功能：[[http://localhost:8000/docs](http://localhost:8000/docs](http://localhost:8000/docs)。
