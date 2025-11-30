# 介绍(Introduction)

Sanic 是 Python 3.9+ 网页服务器和网页框架，这是写得快的。 它允许使用 Python3.5 中添加的 <code>async</code>/<code>await</code> 异步语法，这使得您的代码有效地避免阻塞从而达到提升响应速度的目的。

.. attrs::
:class: introduction-table

```
|  |  |
|--|--|
| Build    | [![Tests](https://github.com/sanic-org/sanic/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/sanic-org/sanic/actions/workflows/tests.yml) |
| Docs     | [![User Guide](https://img.shields.io/badge/user%20guide-sanic-ff0068)](https://sanicframework.org/) [![Documentation](https://readthedocs.org/projects/sanic/badge/?version=latest)](http://sanic.readthedocs.io/en/latest/?badge=latest) |
| Package  | [![PyPI](https://img.shields.io/pypi/v/sanic.svg)](https://pypi.python.org/pypi/sanic/) [![PyPI version](https://img.shields.io/pypi/pyversions/sanic.svg)](https://pypi.python.org/pypi/sanic/) [![Wheel](https://img.shields.io/pypi/wheel/sanic.svg)](https://pypi.python.org/pypi/sanic) [![Supported implementations](https://img.shields.io/pypi/implementation/sanic.svg)](https://pypi.python.org/pypi/sanic) [![Code style black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black) |
| Support  | [![Forums](https://img.shields.io/badge/forums-community-ff0068.svg)](https://community.sanicframework.org/) [![Discord](https://img.shields.io/discord/812221182594121728?logo=discord)](https://discord.gg/FARQzAEMAA) [![Awesome](https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/mekicha/awesome-sanic) |
| Stats    | [![Monthly Downloads](https://img.shields.io/pypi/dm/sanic.svg)](https://pepy.tech/project/sanic) [![Weekly Downloads](https://img.shields.io/pypi/dw/sanic.svg)](https://pepy.tech/project/sanic) [![Conda downloads](https://img.shields.io/conda/dn/conda-forge/sanic.svg)](https://anaconda.org/conda-forge/sanic) |
```

## 是什么？(What is it?)

首先，在入坑之前， 您应该知道 Sanic 框架和其他的框架相比是与众不同的。

Sanic 不仅仅是一个**框架（framework）**，更是一个**服务器（web server）** 我们将在部署（deployment ）章节更多地谈论这个问题。

但是，请记住，Sanic 具备开箱即用的功能，它可以用于编写，部署和扩展生产级 Web 应用程序。 🚀

## 目标

> 提供一种简单且快速，集创建和启动于一体的方法，来实现一个易于修改和拓展的 HTTP 服务器

## 功能(Features)

.. column::

```
### 核心(Core)

- 内置高性能的web server
- 生产就绪
- 高度可扩展性
- 遵循 ASGI 规范
- 简单直观的API设计
- 由社区强力驱动
```

.. column::

```
### 扩展(Sanic Extensions) [[learn more](../plugins/sanic-ext/getting-started.md)]

- **CORS** 保护
- 使用 **Jinja** 进行模板渲染
- 将其他对象通过 **Dependency injection** （依赖注入）到路由处理程序中
- 使用 **Redoc** 和/或 **Swagger** 编写 OpenAPI 文档
- 预先定义好的**序列化函数**(eg `json` `text`)、作用于不同的路由入口（serializers）
- 请求查询参数和正文输入的**验证器**（validation）
- **自动创建** HEAD、OPTIONS 和 TRACE 入口（auto create）
```

## 赞助商

[点击这里](https://opencollective.com/sanic-org)来了解更多关于帮助融资Sanic的信息。

## 加入社区

讨论的主要渠道是[社区论坛](https://community.sanicframework.org/)。 还有一个 [Discord 聊天室](https://discord.gg/RARQzAEMAA) 进行现场讨论和聊天。

Stackoverflow \`[sanic]' 标签由项目维护者[积极关注](https://stackoverflow.com/questions/tagged/sanic)。

## 贡献

我们非常欢迎新的贡献者加入。 我们[有很清晰的issue标记对于那些想要快速上手的人](https://github.com/sanic-org/sanic/issues?q=is%3Aopen+is%3Aissue+label%3Abeginner)，欢迎[ 在社区上提问/回答/讨论](https://community.sanicframework.org/)。 请查看我们的[贡献指南](https://github.com/sanic-org/sanic/blob/master/CONTRIBUTING.rst)。
