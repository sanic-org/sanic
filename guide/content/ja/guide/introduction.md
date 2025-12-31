# はじめに

Sanic is a Python 3.10+ web server and web framework that's written to go fast. Python 3.5 で追加された async/await 構文を使用することができます。これにより、コードをノンブロッキングでスピーディーにすることができます。

.. attrs::
:class: 紹介テーブル

```
|  |  |
|--|--|
| Build    | [![Tests](https://github.com/sanic-org/sanic/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/sanic-org/sanic/actions/workflows/tests.yml) |
| Docs     | [![User Guide](https://img.shields.io/badge/user%20guide-sanic-ff0068)](https://sanicframework.org/) [![Documentation](https://readthedocs.org/projects/sanic/badge/?version=latest)](http://sanic.readthedocs.io/en/latest/?badge=latest) |
| Package  | [![PyPI](https://img.shields.io/pypi/v/sanic.svg)](https://pypi.python.org/pypi/sanic/) [![PyPI version](https://img.shields.io/pypi/pyversions/sanic.svg)](https://pypi.python.org/pypi/sanic/) [![Wheel](https://img.shields.io/pypi/wheel/sanic.svg)](https://pypi.python.org/pypi/sanic) [![Supported implementations](https://img.shields.io/pypi/implementation/sanic.svg)](https://pypi.python.org/pypi/sanic) [![Code style black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black) |
| Support  | [![Forums](https://img.shields.io/badge/forums-community-ff0068.svg)](https://community.sanicframework.org/) [![Discord](https://img.shields.io/discord/812221182594121728?logo=discord)](https://discord.gg/FARQzAEMAA) [![Awesome](https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/mekicha/awesome-sanic) |
| Stats    | [![Monthly Downloads](https://img.shields.io/pypi/dm/sanic.svg)](https://pepy.tech/project/sanic) [![Weekly Downloads](https://img.shields.io/pypi/dw/sanic.svg)](https://pepy.tech/project/sanic) [![Conda downloads](https://img.shields.io/conda/dn/conda-forge/sanic.svg)](https://anaconda.org/conda-forge/sanic) |
```

## それは何ですか?

まず最初に、水に飛び込む前に、Sanicは他のフレームワークとは異なることを知っておくべきです。

最初の文には大きな間違いがあります。なぜなら、Sanic は **framework** と **web server** の両方であるからです。 展開セクションでは、これについてもう少し詳しく説明します。

しかし、Sanicには、プロダクショングレードのWebアプリケーションを作成、デプロイ、およびスケーリングするために必要なものがすべて揃っています。 🚀

## 目標

> 構築しやすい高性能な HTTP サーバーを立ち上げて実行する簡単な方法を提供します。 拡大し最終的には拡大しました

## 特徴

.. 列::

```
### Core

- Built in, **_fast_** web server
- Production ready
- Highly scalable
- ASGI compliant
- Simple and intuitive API design
- By the community, for the community
```

.. 列::

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

## スポンサー情報

format@@0(https://opencollective.com/sanic-org) をご覧ください。

## コミュニティに参加する

ディスカッションの主なチャンネルは、format@@0(https://community.sanicframework.org/)にあります。 ライブディスカッションやチャットのための[Discord Server](https://discord.gg/FARQzAEMAA)もあります。

Stackoverflow `[sanic]` タグはプロジェクトメンテナーによってformat@@1(https://stackoverflow.com/questions/tagged/sanic)です。

## 貢献

私たちは常に新しい貢献をしています。 We have [marked issues good for anyone looking to get started](https://github.com/sanic-org/sanic/issues?q=is%3Aopen+is%3Aissue+label%3Abeginner), and welcome [questions/answers/discussion on the forums](https://community.sanicframework.org/). format@@0(https://github.com/sanic-org/sanic/blob/master/CONTRIBUTING.rst)をご覧ください。
