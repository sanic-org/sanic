Examples
========

This section of the documentation is a simple collection of example code that can help you get a quick start
on your application development. Most of these examples are categorized and provide you with a link to the
working code example in the `Sanic Repository <https://github.com/huge-success/sanic/tree/master/examples>`_


Basic Examples
--------------

This section of the examples are a collection of code that provide a simple use case example of the sanic application.

Simple Apps
~~~~~~~~~~~~

A simple sanic application with a single ``async`` method with ``text`` and ``json`` type response.


.. literalinclude:: ../../examples/teapot.py

.. literalinclude:: ../../examples/simple_server.py


Simple App with ``Sanic Views``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Showcasing the simple mechanism of using :class:`sanic.viewes.HTTPMethodView` as well as a way to extend the same
into providing a custom ``async`` behavior for ``view``.

.. literalinclude:: ../../examples/simple_async_view.py


URL Redirect
~~~~~~~~~~~~

.. literalinclude:: ../../examples/redirect_example.py


Named URL redirection
~~~~~~~~~~~~~~~~~~~~~

``Sanic`` provides an easy to use way of redirecting the requests via a helper method called ``url_for`` that takes a
unique url name as argument and returns you the actual route assigned for it. This will help in simplifying the
efforts required in redirecting the user between different section of the application.

.. literalinclude:: ../../examples/url_for_example.py

Blueprints
~~~~~~~~~~
``Sanic`` provides an amazing feature to group your APIs and routes under a logical collection that can easily be
imported and plugged into any of your sanic application and it's called ``blueprints``

.. literalinclude:: ../../examples/blueprints.py

Logging Enhancements
~~~~~~~~~~~~~~~~~~~~

Even though ``Sanic`` comes with a battery of Logging support it allows the end users to customize the way logging
is handled in the application runtime.

.. literalinclude:: ../../examples/override_logging.py

The following sample provides an example code that demonstrates the usage of :func:`sanic.app.Sanic.middleware` in order
to provide a mechanism to assign a unique request ID for each of the incoming requests and log them via
`aiotask-context <https://github.com/Skyscanner/aiotask-context>`_.


.. literalinclude:: ../../examples/log_request_id.py

Sanic Streaming Support
~~~~~~~~~~~~~~~~~~~~~~~

``Sanic`` framework comes with in-built support for streaming large files and the following code explains the process
to setup a ``Sanic`` application with streaming support.

.. literalinclude:: ../../examples/request_stream/server.py

Sample Client app to show the usage of streaming application by a client code.

.. literalinclude:: ../../examples/request_stream/client.py

Sanic Concurrency Support
~~~~~~~~~~~~~~~~~~~~~~~~~
``Sanic`` supports the ability to start an app with multiple worker support. However, it's important to be able to limit
the concurrency per process/loop in order to ensure an efficient execution. The following section of the code provides a
brief example of how to limit the concurrency with the help of :class:`asyncio.Semaphore`

.. literalinclude:: ../../examples/limit_concurrency.py


Sanic Deployment via Docker
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Deploying a ``sanic`` app via ``docker`` and ``docker-compose`` is an easy task to achieve and the following example
provides a deployment of the sample ``simple_server.py``

.. literalinclude:: ../../examples/Dockerfile

.. literalinclude:: ../../examples/docker-compose.yml


Monitoring and Error Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
``Sanic`` provides an extendable bare minimum implementation of a global exception handler via
:class:`sanic.handlers.ErrorHandler`. This example shows how to extend it to enable some custom behaviors.

.. literalinclude:: ../../examples/exception_monitoring.py

Monitoring using external Service Providers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* `LogDNA <https://logdna.com/>`_

.. literalinclude:: ../../examples/logdna_example.py

* `RayGun <https://raygun.com/>`_

.. literalinclude:: ../../examples/raygun_example.py

* `Rollbar <https://rollbar.com>`_

.. literalinclude:: ../../examples/rollbar_example.py

* `Sentry <http://sentry.io>`_

.. literalinclude:: ../../examples/sentry_example.py


Security
~~~~~~~~

The following sample code shows a simple decorator based authentication and authorization mechanism that can be setup
to secure your ``sanic`` api endpoints.

.. literalinclude:: ../../examples/authorized_sanic.py

Sanic Websocket
~~~~~~~~~~~~~~~

``Sanic`` provides an ability to easily add a route and map it to a ``websocket`` handlers.

.. literalinclude:: ../../examples/websocket.html
.. literalinclude:: ../../examples/websocket.py

vhost Suppport
~~~~~~~~~~~~~~

.. literalinclude:: ../../examples/vhosts.py

Unit Testing With Parallel Test Run Support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following example shows you how to get up and running with unit testing ``sanic`` application with parallel test
execution support provided by the ``pytest-xdist`` plugin.

.. literalinclude:: ../../examples/pytest_xdist.py

For more examples and useful samples please visit the `Huge-Sanic's GitHub Page <https://github.com/huge-success/sanic/tree/master/examples>`_
