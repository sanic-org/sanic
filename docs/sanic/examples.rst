Examples
========

This section of the documentation is a simple collection of example code that can help you get a quick start
on your application development. Most of these examples are categorized and provide you with a link to the
working code example in the `Sanic Repository <https://github.com/huge-success/sanic/tree/master/examples>`_


Basic Examples
--------------

This section of the examples are a collection of code that provide a simple use case example of the sanic application.

Simple Apps
^^^^^^^^^^^

A simple sanic application with a single ``async`` method with ``text`` and ``json`` type response.

.. literalinclude:: ../../examples/teapot.py

.. literalinclude:: ../../examples/simple_server.py


Simple App with ``Sanic Views``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Showcasing the simple mechanism of using :class:`sanic.viewes.HTTPMethodView` as well as a way to extend the same
into providing a custom ``async`` behavior for ``view``.

.. literalinclude:: ../../examples/simple_async_view.py


URL Redirect
^^^^^^^^^^^^

.. literalinclude:: ../../examples/redirect_example.py


Named URL redirection
^^^^^^^^^^^^^^^^^^^^^

``Sanic`` provides an easy to use way of redirecting the requests via a helper method called ``url_for`` that takes a
unique url name as argument and returns you the actual route assigned for it. This will help in simplifying the
efforts required in redirecting the user between different section of the application.

.. literalinclude:: ../../examples/url_for_example.py

Custom Logging
^^^^^^^^^^^^^^

Even though ``Sanic`` comes with a battery of Logging support it allows the end users to customize the way logging
is handled in the application runtime.

.. literalinclude:: ../../examples/override_logging.py


