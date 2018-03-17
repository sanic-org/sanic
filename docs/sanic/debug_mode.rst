Debug Mode
=============

When enabling Sanic's debug mode, Sanic will provide a more verbose logging output
and by default will enable the Auto Reload feature.

.. warning::

    Sanic's debug more will slow down the server's performance
    and is therefore advised to enable it only in development environments.


Setting the debug mode
----------------------

By setting the ``debug`` mode a more verbose output from Sanic will be outputed
and the Automatic Reloader will be activated.

.. code-block:: python

    from sanic import Sanic
    from sanic.response import json

    app = Sanic()

    @app.route('/')
    async def hello_world(request):
        return json({"hello": "world"})

    if __name__ == '__main__':
        app.run(host="0.0.0.0", port=8000, debug=True)



Manually setting auto reload
----------------------------

Sanic offers a way to enable or disable the Automatic Reloader manually,
the ``auto_reload`` argument will activate or deactivate the Automatic Reloader.

.. code-block:: python

    from sanic import Sanic
    from sanic.response import json

    app = Sanic()

    @app.route('/')
    async def hello_world(request):
        return json({"hello": "world"})

    if __name__ == '__main__':
        app.run(host="0.0.0.0", port=8000, auto_reload=True)