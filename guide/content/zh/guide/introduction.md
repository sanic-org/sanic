# 一. 导言

Sanic 是 Python 的 3.8+ 网页服务器和网页框架，它写得更快。 它允许使用 Python 3.5中添加的异步/等待语法，这使您的代码不受阻挡和快速。

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

## 什么是？

首先，在你跳进水面之前，你应该知道Sanic与其他框架不同。

就在第一句中，因为Sanic 是 _both_a **framework** 和 **web server** 。 我们将在部署部分更多地谈论这个问题。

但请记住，Sanic 从盒子中带有你需要写、部署和缩放生产级网页应用程序的一切。 🚀

## 目标

> 提供一个简单的方式来启动和运行一个易于构建的高性能的 HTTP 服务器， 扩大并最终扩大规模。

## 功能

.. 列:

```
### Core

- Built in, **_fast_** web server
- Production ready
- Highly scalable
- ASGI compliant
- Simple and intuitive API design
- By the community, for the community
```

.. 列:

```
### Sanic Extensions [[learn more](../plugins/sanic-ext/getting-started.md)]

- CORS protection
- Template rendering with Jinja
- Dependency injection into route handlers
- OpenAPI documentation with Redoc and/or Swagger
- Predefined, endpoint-specific response serializers
- Request query arguments and body input validation
- Auto create `HEAD`, `OPTIONS`, and `TRACE` endpoints
```

## 赞助商

查看[打开集体](https://opencollective.com/sanic-org)来了解更多关于帮助融资Sanic的信息。

## 加入社区

讨论的主要渠道是[社区论坛](https://community.sanicframework.org/)。 还有一个 [Discord 服务器](https://discord.gg/RARQzAEMAA) 进行现场讨论和聊天。

Stackoverflow \`[sanic]' 标签由项目维护者[积极监视](https://stackoverflow.com/questions/tagged/sanic)。

## 贡献

我们总是乐于得到新的捐助。 我们有[标记的问题对任何想要开始的人来说都是好的](https://github.com/sanic-org/sanic/issues?q=is%3Aopen+is%3Aissue+label%3Abeginner)，欢迎[questions/answers/discussion on on the forums](https://community.sanicframework.org/)。 请查看我们的[贡献指南](https://github.com/sanic-org/sanic/blob/master/CONTRIBUTING.rst)。
