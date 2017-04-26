Sanic
=================================

|Join the chat at https://gitter.im/sanic-python/Lobby| |Build Status| |PyPI| |PyPI version|

Sanic is a Flask-like Python 3.5+ web server that's written to go fast.  It's based on the work done by the amazing folks at magicstack, and was inspired by `this article <https://magic.io/blog/uvloop-blazing-fast-python-networking/>`_.

On top of being Flask-like, Sanic supports async request handlers.  This means you can use the new shiny async/await syntax from Python 3.5, making your code non-blocking and speedy.

Sanic is developed `on GitHub <https://github.com/channelcat/sanic/>`_. Contributions are welcome!

If you have a project that utilizes Sanic make sure to comment on the `issue <https://github.com/channelcat/sanic/issues/396>`_ that we use to track those projects!

Benchmarks
----------

All tests were run on an AWS medium instance running ubuntu, using 1
process. Each script delivered a small JSON response and was tested with
wrk using 100 connections. Pypy was tested for Falcon and Flask but did
not speed up requests.

+-----------+-----------------------+----------------+---------------+
| Server    | Implementation        | Requests/sec   | Avg Latency   |
+===========+=======================+================+===============+
| Sanic     | Python 3.5 + uvloop   | 33,342         | 2.96ms        |
+-----------+-----------------------+----------------+---------------+
| Wheezy    | gunicorn + meinheld   | 20,244         | 4.94ms        |
+-----------+-----------------------+----------------+---------------+
| Falcon    | gunicorn + meinheld   | 18,972         | 5.27ms        |
+-----------+-----------------------+----------------+---------------+
| Bottle    | gunicorn + meinheld   | 13,596         | 7.36ms        |
+-----------+-----------------------+----------------+---------------+
| Flask     | gunicorn + meinheld   | 4,988          | 20.08ms       |
+-----------+-----------------------+----------------+---------------+
| Kyoukai   | Python 3.5 + uvloop   | 3,889          | 27.44ms       |
+-----------+-----------------------+----------------+---------------+
| Aiohttp   | Python 3.5 + uvloop   | 2,979          | 33.42ms       |
+-----------+-----------------------+----------------+---------------+
| Tornado   | Python 3.5            | 2,138          | 46.66ms       |
+-----------+-----------------------+----------------+---------------+

Hello World Example
-------------------

.. code:: python

    from sanic import Sanic
    from sanic.response import json

    app = Sanic()

    @app.route("/")
    async def test(request):
        return json({"hello": "world"})

    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=8000)

Installation
------------

-  ``python -m pip install sanic``

To install sanic without uvloop or json using bash, you can provide either or both of these environmental variables
using any truthy string like `'y', 'yes', 't', 'true', 'on', '1'` and setting the NO_X to true will stop that features
installation.

- ``SANIC_NO_UVLOOP=true SANIC_NO_UJSON=true python -m pip install sanic``


Documentation
-------------

`Documentation on Readthedocs <http://sanic.readthedocs.io/>`_.

.. |Join the chat at https://gitter.im/sanic-python/Lobby| image:: https://badges.gitter.im/sanic-python/Lobby.svg
   :target: https://gitter.im/sanic-python/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge
.. |Build Status| image:: https://travis-ci.org/channelcat/sanic.svg?branch=master
   :target: https://travis-ci.org/channelcat/sanic
.. |Documentation| image:: https://readthedocs.org/projects/sanic/badge/?version=latest
   :target: http://sanic.readthedocs.io/en/latest/?badge=latest
.. |PyPI| image:: https://img.shields.io/pypi/v/sanic.svg
   :target: https://pypi.python.org/pypi/sanic/
.. |PyPI version| image:: https://img.shields.io/pypi/pyversions/sanic.svg
   :target: https://pypi.python.org/pypi/sanic/

TODO
----
* Streamed file processing
* http2
Limitations
-----------
* No wheels for uvloop and httptools on Windows :(

Final Thoughts
--------------

::

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
