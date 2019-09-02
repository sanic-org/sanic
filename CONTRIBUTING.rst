
Contributing
============

Thank you for your interest! Sanic is always looking for contributors. If you
don't feel comfortable contributing code, adding docstrings to the source files
is very appreciated.

We are committed to providing a friendly, safe and welcoming environment for all,
regardless of gender, sexual orientation, disability, ethnicity, religion,
or similar personal characteristic.
Our `code of conduct <./CONDUCT.md>`_ sets the standards for behavior.

Installation
------------

To develop on sanic (and mainly to just run the tests) it is highly recommend to
install from sources.

So assume you have already cloned the repo and are in the working directory with
a virtual environment already set up, then run:

.. code-block:: bash

   pip3 install -e . ".[dev]"

Dependency Changes
------------------

``Sanic`` doesn't use ``requirements*.txt`` files to manage any kind of dependencies related to it in order to simplify the
effort required in managing the dependencies. Please make sure you have read and understood the following section of
the document that explains the way ``sanic`` manages dependencies inside the ``setup.py`` file.

.. list-table::
   :header-rows: 1

   * - Dependency Type
     - Usage
     - Installation
   * - requirements
     - Bare minimum dependencies required for sanic to function
     - ``pip3 install -e .``
   * - tests_require / extras_require['test']
     - Dependencies required to run the Unit Tests for ``sanic``
     - ``pip3 install -e '.[test]'``
   * - extras_require['dev']
     - Additional Development requirements to add contributing
     - ``pip3 install -e '.[dev]'``
   * - extras_require['docs']
     - Dependencies required to enable building and enhancing sanic documentation
     - ``pip3 install -e '.[docs]'``


Running all tests
-----------------

To run the tests for Sanic it is recommended to use tox like so:

.. code-block:: bash

   tox

See it's that simple!

``tox.ini`` contains different environments. Running ``tox`` without any arguments will
run all unittests, perform lint and other checks.

Run unittests
-------------

``tox`` environment -> ``[testenv]`

To execute only unittests, run ``tox`` with environment like so:

.. code-block:: bash

   tox -e py36 -v -- tests/test_config.py
   # or
   tox -e py37 -v -- tests/test_config.py

Run lint checks
---------------

``tox`` environment -> ``[testenv:lint]``

Permform ``flake8``\ , ``black`` and ``isort`` checks.

.. code-block:: bash

   tox -e lint

Run other checks
----------------

``tox`` environment -> ``[testenv:check]``

Perform other checks.

.. code-block:: bash

   tox -e check

Run Static Analysis
-------------------

``tox`` environment -> ``[testenv:security]``

Perform static analysis security scan

.. code-block:: bash

   tox -e security

Run Documentation sanity check
------------------------------

``tox`` environment -> ``[testenv:docs]``

Perform sanity check on documentation

.. code-block:: bash

   tox -e docs


Code Style
----------

To maintain the code consistency, Sanic uses following tools.


#. `isort <https://github.com/timothycrosley/isort>`_
#. `black <https://github.com/python/black>`_
#. `flake8 <https://github.com/PyCQA/flake8>`_

isort
*****

``isort`` sorts Python imports. It divides imports into three
categories sorted each in alphabetical order.


#. built-in
#. third-party
#. project-specific

black
*****

``black`` is a Python code formatter.

flake8
******

``flake8`` is a Python style guide that wraps following tools into one.


#. PyFlakes
#. pycodestyle
#. Ned Batchelder's McCabe script

``isort``\ , ``black`` and ``flake8`` checks are performed during ``tox`` lint checks.

Refer `tox <https://tox.readthedocs.io/en/latest/index.html>`_ documentation for more details.

Pull requests
-------------

So the pull request approval rules are pretty simple:

#. All pull requests must have a changelog details associated with it.
#. All pull requests must pass unit tests.
#. All pull requests must be reviewed and approved by at least one current collaborator on the project.
#. All pull requests must pass flake8 checks.
#. All pull requests must be consistent with the existing code.
#. If you decide to remove/change anything from any common interface a deprecation message should accompany it.
#. If you implement a new feature you should have at least one unit test to accompany it.
#. An example must be one of the following:

   * Example of how to use Sanic
   * Example of how to use Sanic extensions
   * Example of how to use Sanic and asynchronous library


Changelog
---------

It is mandatory to add documentation for Change log as part of your Pull request when you fix/contribute something
to the ``sanic`` community. This will enable us in generating better and well defined change logs during the
release which can aid community users in a great way.

.. note::

    Single line explaining the details of the PR in brief

    Detailed description of what the PR is about and what changes or enhancements are being done.
    No need to include examples or any other details here. But it is important that you provide
    enough context here to let user understand what this change is all about and why it is being
    introduced into the ``sanic`` codebase.

    Make sure you leave an line space after the first line to make sure the document rendering is clean


.. list-table::
   :header-rows: 1

   * - Contribution Type
     - Changelog file name format
     - Changelog file location
   * - Features
     - <git_issue>.feature.rst
     - ``changelogs``
   * - Bugfixes
     - <git_issue>.bugfix.rst
     - ``changelogs``
   * - Improved Documentation
     - <git_issue>.doc.rst
     - ``changelogs``
   * - Deprecations and Removals
     - <git_issue>.removal.rst
     - ``changelogs``
   * - Miscellaneous internal changes
     - <git_issue>.misc.rst
     - ``changelogs``


Documentation
-------------

Sanic's documentation is built
using `sphinx <http://www.sphinx-doc.org/en/1.5.1/>`_. Guides are written in
Markdown and can be found in the ``docs`` folder, while the module reference is
automatically generated using ``sphinx-apidoc``.

To generate the documentation from scratch:

.. code-block:: bash

   sphinx-apidoc -fo docs/_api/ sanic
   sphinx-build -b html docs docs/_build

   # There is a simple make command provided to ease the work required in generating
   # the documentation
   make docs

The HTML documentation will be created in the ``docs/_build`` folder.

.. warning::
   One of the main goals of Sanic is speed. Code that lowers the performance of
   Sanic without significant gains in usability, security, or features may not be
   merged. Please don't let this intimidate you! If you have any concerns about an
   idea, open an issue for discussion and help.
