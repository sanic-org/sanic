# Sanic

[![Join the chat at https://gitter.im/sanic-python/Lobby](https://badges.gitter.im/sanic-python/Lobby.svg)](https://gitter.im/sanic-python/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

[![Build Status](https://travis-ci.org/channelcat/sanic.svg?branch=master)](https://travis-ci.org/channelcat/sanic)
[![PyPI](https://img.shields.io/pypi/v/sanic.svg)](https://pypi.python.org/pypi/sanic/)
[![PyPI](https://img.shields.io/pypi/pyversions/sanic.svg)](https://pypi.python.org/pypi/sanic/)

Sanic is a Flask-like Python 3.5+ web server that's written to go fast.  It's based on the work done by the amazing folks at magicstack, and was inspired by this article: https://magic.io/blog/uvloop-blazing-fast-python-networking/.

On top of being Flask-like, Sanic supports async request handlers.  This means you can use the new shiny async/await syntax from Python 3.5, making your code non-blocking and speedy.

## Benchmarks

All tests were run on an AWS medium instance running ubuntu, using 1 process.  Each script delivered a small JSON response and was tested with wrk using 100 connections.  Pypy was tested for Falcon and Flask but did not speed up requests.



| Server  | Implementation      | Requests/sec | Avg Latency |
| ------- | ------------------- | ------------:| -----------:|
| Sanic   | Python 3.5 + uvloop |       33,342 |      2.96ms |
| Wheezy  | gunicorn + meinheld |       20,244 |      4.94ms |
| Falcon  | gunicorn + meinheld |       18,972 |      5.27ms |
| Bottle  | gunicorn + meinheld |       13,596 |      7.36ms |
| Flask   | gunicorn + meinheld |        4,988 |     20.08ms |
| Kyoukai | Python 3.5 + uvloop |        3,889 |     27.44ms |
| Aiohttp | Python 3.5 + uvloop |        2,979 |     33.42ms |
| Tornado | Python 3.5          |        2,138 |     46.66ms |

## Hello World

```python
from sanic import Sanic
from sanic.response import json

app = Sanic()

@app.route("/")
async def test(request):
    return json({"hello": "world"})

app.run(host="0.0.0.0", port=8000)
```

## Installation
 * `python -m pip install sanic`

## Documentation
 * [Getting started](docs/getting_started.md)
 * [Request Data](docs/request_data.md)
 * [Routing](docs/routing.md)
 * [Middleware](docs/middleware.md)
 * [Exceptions](docs/exceptions.md)
 * [Blueprints](docs/blueprints.md)
 * [Class Based Views](docs/class_based_views.md)
 * [Cookies](docs/cookies.md)
 * [Static Files](docs/static_files.md)
 * [Deploying](docs/deploying.md)
 * [Contributing](docs/contributing.md)
 * [License](LICENSE)

## TODO:
 * Streamed file processing
 * File output
 * Examples of integrations with 3rd-party modules
 * RESTful router

## Limitations:
 * No wheels for uvloop and httptools on Windows :(

## Final Thoughts:

                     ▄▄▄▄▄
            ▀▀▀██████▄▄▄       _______________
          ▄▄▄▄▄  █████████▄  /                 \
         ▀▀▀▀█████▌ ▀▐▄ ▀▐█ |   Gotta go fast!  |
       ▀▀█████▄▄ ▀██████▄██ | _________________/
       ▀▄▄▄▄▄  ▀▀█▄▀█════█▀ |/
            ▀▀▀▄  ▀▀███ ▀       ▄▄
         ▄███▀▀██▄████████▄ ▄▀▀▀▀▀▀█▌
       ██▀▄▄▄██▀▄███▀ ▀▀████      ▄██
    ▄▀▀▀▄██▄▀▀▌████▒▒▒▒▒▒███     ▌▄▄▀
    ▌    ▐▀████▐███▒▒▒▒▒▐██▌
    ▀▄▄▄▄▀   ▀▀████▒▒▒▒▄██▀
              ▀▀█████████▀
            ▄▄██▀██████▀█
          ▄██▀     ▀▀▀  █
         ▄█             ▐▌
     ▄▄▄▄█▌              ▀█▄▄▄▄▀▀▄
    ▌     ▐                ▀▀▄▄▄▀
     ▀▀▄▄▀
