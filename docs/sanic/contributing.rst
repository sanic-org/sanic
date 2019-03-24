Contributing
============

Thank you for your interest! Sanic is always looking for contributors.
If you don’t feel comfortable contributing code, adding docstrings to
the source files is very appreciated.

Installation
------------

To develop on sanic (and mainly to just run the tests) it is highly
recommend to install from sources.

So assume you have already cloned the repo and are in the working
directory with a virtual environment already set up, then run:

.. code:: bash

   pip3 install -e '.[dev]'

Dependency Changes
------------------

``Sanic`` doesn't use ``requirements*.txt`` files to manage any kind of dependencies related to it in order to simplify the
effort required in managing the dependencies. Please make sure you have read and understood the following section of
the document that explains the way ``sanic`` manages dependencies inside the ``setup.py`` file.

+------------------------+-----------------------------------------------+--------------------------------+
| Dependency Type        | Usage                                         | Installation                   |
+========================+===============================================+================================+
| requirements           | Bare minimum dependencies required for sanic  | ``pip3 install -e .``          |
|                        | to function                                   |                                |
+------------------------+-----------------------------------------------+--------------------------------+
| tests_require /        | Dependencies required to run the Unit Tests   | ``pip3 install -e '.[test]'``  |
| extras_require['test'] | for ``sanic``                                 |                                |
+------------------------+-----------------------------------------------+--------------------------------+
| extras_require['dev']  | Additional Development requirements to add    | ``pip3 install -e '.[dev]'``   |
|                        | for contributing                              |                                |
+------------------------+-----------------------------------------------+--------------------------------+
| extras_require['docs'] | Dependencies required to enable building and  | ``pip3 install -e '.[docs]'``  |
|                        | enhancing sanic documentation                 |                                |
+------------------------+-----------------------------------------------+--------------------------------+

Running tests
-------------

To run the tests for sanic it is recommended to use tox like so:

.. code:: bash

   tox

See it’s that simple!

Pull requests!
--------------

So the pull request approval rules are pretty simple:

* All pull requests must pass unit tests
* All pull requests must be reviewed and approved by at least one current collaborator on the project
* All pull requests must pass flake8 checks
* If you decide to remove/change anything from any common interface a deprecation message should accompany it.
* If you implement a new feature you should have at least one unit test to accompany it.

Documentation
-------------

Sanic’s documentation is built using `sphinx`_. Guides are written in
Markdown and can be found in the ``docs`` folder, while the module
reference is automatically generated using ``sphinx-apidoc``.

To generate the documentation from scratch:

.. code:: bash

   sphinx-apidoc -fo docs/_api/ sanic
   sphinx-build -b html docs docs/_build

The HTML documentation will be created in the ``docs/_build`` folder.

.. warning::
    One of the main goals of Sanic is speed. Code that lowers the
    performance of Sanic without significant gains in usability, security,
    or features may not be merged. Please don’t let this intimidate you! If
    you have any concerns about an idea, open an issue for discussion and
    help.

.. _sphinx: http://www.sphinx-doc.org/en/1.5.1/