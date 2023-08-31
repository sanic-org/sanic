# Introduction

Sanic is a Python 3.7+ web server and web framework that’s written to go fast. It allows the usage of the async/await syntax added in Python 3.5, which makes your code non-blocking and speedy.

.. attrs::
    :class: introduction-table

    |  |  |
    |--|--|
    | Build    | [![Tests](https://github.com/sanic-org/sanic/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/sanic-org/sanic/actions/workflows/tests.yml) |
    | Docs     | [![User Guide](https://img.shields.io/badge/user%20guide-sanic-ff0068)](https://sanicframework.org/) [![Documentation](https://readthedocs.org/projects/sanic/badge/?version=latest)](http://sanic.readthedocs.io/en/latest/?badge=latest) |
    | Package  | [![PyPI](https://img.shields.io/pypi/v/sanic.svg)](https://pypi.python.org/pypi/sanic/) [![PyPI version](https://img.shields.io/pypi/pyversions/sanic.svg)](https://pypi.python.org/pypi/sanic/) [![Wheel](https://img.shields.io/pypi/wheel/sanic.svg)](https://pypi.python.org/pypi/sanic) [![Supported implementations](https://img.shields.io/pypi/implementation/sanic.svg)](https://pypi.python.org/pypi/sanic) [![Code style black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black) |
    | Support  | [![Forums](https://img.shields.io/badge/forums-community-ff0068.svg)](https://community.sanicframework.org/) [![Discord](https://img.shields.io/discord/812221182594121728?logo=discord)](https://discord.gg/FARQzAEMAA) [![Awesome](https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/mekicha/awesome-sanic) |
    | Stats    | [![Monthly Downloads](https://img.shields.io/pypi/dm/sanic.svg)](https://pepy.tech/project/sanic) [![Weekly Downloads](https://img.shields.io/pypi/dw/sanic.svg)](https://pepy.tech/project/sanic) [![Conda downloads](https://img.shields.io/conda/dn/conda-forge/sanic.svg)](https://anaconda.org/conda-forge/sanic) |



## What is it?

First things first, before you jump in the water, you should know that Sanic is different than other frameworks.

Right there in that first sentence there is a huge mistake because Sanic is _both_ a **framework** and a **web server**. In the deployment section we will talk a little bit more about this. 

But, remember, out of the box Sanic comes with everything you need to write, deploy, and scale a production grade web application. :rocket:

## Goal

> To provide a simple way to get up and running a highly performant HTTP server that is easy to build, to expand, and ultimately to scale.
## Features

.. column::

    ### Core

    - Built in, **_fast_** web server
    - Production ready
    - Highly scalable
    - ASGI compliant
    - Simple and intuitive API design
    - By the community, for the community

.. column::

    ### Sanic Extensions [[learn more](../plugins/sanic-ext/getting-started.md)]

    - CORS protection
    - Template rendering with Jinja
    - Dependency injection into route handlers
    - OpenAPI documentation with Redoc and/or Swagger
    - Predefined, endpoint-specific response serializers
    - Request query arguments and body input validation
    - Auto create `HEAD`, `OPTIONS`, and `TRACE` endpoints

## Sponsor

Check out [open collective](https://opencollective.com/sanic-org) to learn more about helping to fund Sanic.


## Join the Community

The main channel for discussion is at the [community forums](https://community.sanicframework.org/). There also is a [Discord Server](https://discord.gg/FARQzAEMAA) for live discussion and chat.

The Stackoverflow `[sanic]` tag is [actively monitored](https://stackoverflow.com/questions/tagged/sanic) by project maintainers.

## Contribution

We are always happy to have new contributions. We have [marked issues good for anyone looking to get started](https://github.com/sanic-org/sanic/issues?q=is%3Aopen+is%3Aissue+label%3Abeginner), and welcome [questions/answers/discussion on the forums](https://community.sanicframework.org/). Please take a look at our [Contribution guidelines](https://github.com/sanic-org/sanic/blob/master/CONTRIBUTING.rst).
