Getting Started
===============

Make sure you have both `pip <https://pip.pypa.io/en/stable/installing/>`_ and at
least version 3.6 of Python before starting. Sanic uses the new `async`/`await`
syntax, so earlier versions of python won't work.

1. Install Sanic
----------------

>   If you are running on a clean install of Fedora 28 or above, please make sure you have the ``redhat-rpm-config`` package installed in case if you want to use ``sanic`` with ``ujson`` dependency.

.. code-block:: bash

    pip3 install sanic

To install sanic without `uvloop` or `ujson` using bash, you can provide either or both of these environmental variables
using any truthy string like `'y', 'yes', 't', 'true', 'on', '1'` and setting the `SANIC_NO_X` (`X` = `UVLOOP`/`UJSON`)
to true will stop that features installation.

.. code-block:: bash

    SANIC_NO_UVLOOP=true SANIC_NO_UJSON=true pip3 install --no-binary :all: sanic

You can also install Sanic from `conda-forge <https://anaconda.org/conda-forge/sanic>`_

.. code-block:: bash

    conda config --add channels conda-forge
    conda install sanic

2. Create a file called `main.py`
---------------------------------

.. code-block:: python

    from sanic import Sanic
    from sanic.response import json

    app = Sanic()

    @app.route("/")
    async def test(request):
      return json({"hello": "world"})

    if __name__ == "__main__":
      app.run(host="0.0.0.0", port=8000)

3. Run the server
-----------------

.. code-block:: bash

    python3 main.py

4. Check your browser
---------------------

Open the address `http://0.0.0.0:8000 <http://0.0.0.0:8000>`_ in your web browser. You should see
the message *Hello world!*.

You now have a working Sanic server!
