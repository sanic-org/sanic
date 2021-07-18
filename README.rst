.. image:: https://raw.githubusercontent.com/sanic-org/sanic-assets/master/png/sanic-framework-logo-400x97.png
    :alt: Sanic | Build fast. Run fast.

Sanic | Build fast. Run fast.
=============================

.. start-badges

.. list-table::
    :widths: 15 85
    :stub-columns: 1

    * - Build
      - | |Py39Test| |Py38Test| |Py37Test| |Codecov|
    * - Docs
      - | |UserGuide| |Documentation|
    * - Package
      - | |PyPI| |PyPI version| |Wheel| |Supported implementations| |Code style black|
    * - Support
      - | |Forums| |Discord| |Awesome|
    * - Stats
      - | |Downloads| |WkDownloads| |Conda downloads|

.. |UserGuide| image:: https://img.shields.io/badge/user%20guide-sanic-ff0068
   :target: https://sanicframework.org/
.. |Forums| image:: https://img.shields.io/badge/forums-community-ff0068.svg
   :target: https://community.sanicframework.org/
.. |Discord| image:: https://img.shields.io/discord/812221182594121728?logo=discord
   :target: https://discord.gg/FARQzAEMAA
.. |Codecov| image:: https://codecov.io/gh/sanic-org/sanic/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/sanic-org/sanic
.. |Py39Test| image:: https://github.com/sanic-org/sanic/actions/workflows/pr-python39.yml/badge.svg?branch=main
   :target: https://github.com/sanic-org/sanic/actions/workflows/pr-python39.yml
.. |Py38Test| image:: https://github.com/sanic-org/sanic/actions/workflows/pr-python38.yml/badge.svg?branch=main
   :target: https://github.com/sanic-org/sanic/actions/workflows/pr-python38.yml
.. |Py37Test| image:: https://github.com/sanic-org/sanic/actions/workflows/pr-python37.yml/badge.svg?branch=main
   :target: https://github.com/sanic-org/sanic/actions/workflows/pr-python37.yml
.. |Documentation| image:: https://readthedocs.org/projects/sanic/badge/?version=latest
   :target: http://sanic.readthedocs.io/en/latest/?badge=latest
.. |PyPI| image:: https://img.shields.io/pypi/v/sanic.svg
   :target: https://pypi.python.org/pypi/sanic/
.. |PyPI version| image:: https://img.shields.io/pypi/pyversions/sanic.svg
   :target: https://pypi.python.org/pypi/sanic/
.. |Code style black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/ambv/black
.. |Wheel| image:: https://img.shields.io/pypi/wheel/sanic.svg
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/sanic
.. |Supported implementations| image:: https://img.shields.io/pypi/implementation/sanic.svg
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/sanic
.. |Awesome| image:: https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg
    :alt: Awesome Sanic List
    :target: https://github.com/mekicha/awesome-sanic
.. |Downloads| image:: https://pepy.tech/badge/sanic/month
    :alt: Downloads
    :target: https://pepy.tech/project/sanic
.. |WkDownloads| image:: https://pepy.tech/badge/sanic/week
    :alt: Downloads
    :target: https://pepy.tech/project/sanic
.. |Conda downloads| image:: https://img.shields.io/conda/dn/conda-forge/sanic.svg
    :alt: Downloads
    :target: https://anaconda.org/conda-forge/sanic

.. end-badges

Sanic is a **Python 3.7+** web server and web framework that's written to go fast. It allows the usage of the ``async/await`` syntax added in Python 3.5, which makes your code non-blocking and speedy.

Sanic is also ASGI compliant, so you can deploy it with an `alternative ASGI webserver <https://sanic.readthedocs.io/en/latest/sanic/deploying.html#running-via-asgi>`_.

`Source code on GitHub <https://github.com/sanic-org/sanic/>`_ | `Help and discussion board <https://community.sanicframework.org/>`_ | `User Guide <https://sanicframework.org>`_ | `Chat on Discord <https://discord.gg/FARQzAEMAA>`_

The project is maintained by the community, for the community. **Contributions are welcome!**

The goal of the project is to provide a simple way to get up and running a highly performant HTTP server that is easy to build, to expand, and ultimately to scale.

Sponsor
-------

Check out `open collective <https://opencollective.com/sanic-org>`_ to learn more about helping to fund Sanic.

Installation
------------

``pip3 install sanic``

    Sanic makes use of ``uvloop`` and ``ujson`` to help with performance. If you do not want to use those packages, simply add an environmental variable ``SANIC_NO_UVLOOP=true`` or ``SANIC_NO_UJSON=true`` at install time.

    .. code:: shell

       $ export SANIC_NO_UVLOOP=true
       $ export SANIC_NO_UJSON=true
       $ pip3 install --no-binary :all: sanic


.. note::

  If you are running on a clean install of Fedora 28 or above, please make sure you have the ``redhat-rpm-config`` package installed in case if you want to
  use ``sanic`` with ``ujson`` dependency.

.. note::

  Windows support is currently "experimental" and on a best-effort basis. Multiple workers are also not currently supported on Windows (see `Issue #1517 <https://github.com/sanic-org/sanic/issues/1517>`_), but setting ``workers=1`` should launch the server successfully.

Hello World Example
-------------------

.. code:: python

    from sanic import Sanic
    from sanic.response import json

    app = Sanic("My Hello, world app")

    @app.route('/')
    async def test(request):
        return json({'hello': 'world'})

    if __name__ == '__main__':
        app.run()

Sanic can now be easily run using ``sanic hello.app``.

.. code::

    [2018-12-30 11:37:41 +0200] [13564] [INFO] Goin' Fast @ http://127.0.0.1:8000
    [2018-12-30 11:37:41 +0200] [13564] [INFO] Starting worker [13564]

And, we can verify it is working: ``curl localhost:8000 -i``

.. code::

    HTTP/1.1 200 OK
    Connection: keep-alive
    Keep-Alive: 5
    Content-Length: 17
    Content-Type: application/json

    {"hello":"world"}

**Now, let's go build something fast!**

Minimum Python version is 3.7. If you need Python 3.6 support, please use v20.12LTS.

Documentation
-------------

`User Guide <https://sanicframework.org>`__ and `API Documentation <http://sanic.readthedocs.io/>`__.

Changelog
---------

`Release Changelogs <https://github.com/sanic-org/sanic/blob/master/CHANGELOG.rst>`__.


Questions and Discussion
------------------------

`Ask a question or join the conversation <https://community.sanicframework.org/>`__.

Contribution
------------

We are always happy to have new contributions. We have `marked issues good for anyone looking to get started <https://github.com/sanic-org/sanic/issues?q=is%3Aopen+is%3Aissue+label%3Abeginner>`_, and welcome `questions on the forums <https://community.sanicframework.org/>`_. Please take a look at our `Contribution guidelines <https://github.com/sanic-org/sanic/blob/master/CONTRIBUTING.rst>`_.
