Sanic
=================================

Sanic is a Python 3.6+ web server and web framework that's written to go fast. It allows the usage of the async/await syntax added in Python 3.5, which makes your code non-blocking and speedy.

The goal of the project is to provide a simple way to get up and running a highly performant HTTP server that is easy to build, to expand, and ultimately to scale.

Sanic is developed `on GitHub <https://github.com/channelcat/sanic/>`_. Contributions are welcome!

Sanic aspires to be simple
---------------------------

.. code:: python

    from sanic import Sanic
    from sanic.response import json

    app = Sanic()

    @app.route("/")
    async def test(request):
        return json({"hello": "world"})

    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=8000)

.. note::

    Sanic does not support Python 3.5 from version 19.6 and forward. However, version 18.12LTS is supported thru December 2020. Official Python support for version 3.5 is set to expire in September 2020.