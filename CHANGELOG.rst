Version 20.3.0
===============

Features
********

  * 
    `#1762 <https://github.com/huge-success/sanic/pull/1762>`_
    Add ``srv.start_serving()`` and ``srv.serve_forever()`` to ``AsyncioServer``

  * 
    `#1767 <https://github.com/huge-success/sanic/pull/1767>`_
    Make Sanic usable on ``hypercorn -k trio myweb.app``

  * 
    `#1768 <https://github.com/huge-success/sanic/pull/1768>`_
    No tracebacks on normal errors and prettier error pages

  * 
    `#1769 <https://github.com/huge-success/sanic/pull/1769>`_
    Code cleanup in file responses

  * 
    `#1793 <https://github.com/huge-success/sanic/pull/1793>`_ and
    `#1819 <https://github.com/huge-success/sanic/pull/1819>`_ 
    Upgrade ``str.format()`` to f-strings

  * 
    `#1798 <https://github.com/huge-success/sanic/pull/1798>`_
    Allow multiple workers on MacOS with Python 3.8

  *
    `#1820 <https://github.com/huge-success/sanic/pull/1820>`_
    Do not set content-type and content-length headers in exceptions

Bugfixes
********

  * 
    `#1748 <https://github.com/huge-success/sanic/pull/1748>`_
    Remove loop argument in ``asyncio.Event`` in Python 3.8

  * 
    `#1764 <https://github.com/huge-success/sanic/pull/1764>`_
    Allow route decorators to stack up again

  * 
    `#1789 <https://github.com/huge-success/sanic/pull/1789>`_
    Fix tests using hosts yielding incorrect ``url_for``

  * 
    `#1808 <https://github.com/huge-success/sanic/pull/1808>`_
     Fix Ctrl+C and tests on Windows

Deprecations and Removals
*************************

  *
    `#1800 <https://github.com/huge-success/sanic/pull/1800>`_
    Begin deprecation in way of first-class streaming, removal of ``body_init``, ``body_push``, and ``body_finish``

  *
    `#1801 <https://github.com/huge-success/sanic/pull/1801>`_
    Complete deprecation from `#1666 <https://github.com/huge-success/sanic/pull/1666>`_ of dictionary context on ``request`` objects.
    
  *
    `#1807 <https://github.com/huge-success/sanic/pull/1807>`_
    Remove server config args that can be read directly from app

  *
    `#1818 <https://github.com/huge-success/sanic/pull/1818>`_
    Complete deprecation of ``app.remove_route`` and ``request.raw_args``

Dependencies
************

  *
    `#1794 <https://github.com/huge-success/sanic/pull/1794>`_
    Bump ``httpx`` to 0.11.1

  *
    `#1806 <https://github.com/huge-success/sanic/pull/1806>`_
    Import ``ASGIDispatch`` from top-level ``httpx`` (from third-party deprecation)

Developer infrastructure
************************

  * 
    `#1833 <https://github.com/huge-success/sanic/pull/1833>`_
    Resolve broken documentation builds

Improved Documentation
**********************

  * 
    `#1755 <https://github.com/huge-success/sanic/pull/1755>`_
    Usage of ``response.empty()``

  * 
    `#1778 <https://github.com/huge-success/sanic/pull/1778>`_
    Update README

  * 
    `#1783 <https://github.com/huge-success/sanic/pull/1783>`_
    Fix typo

  *
    `#1784 <https://github.com/huge-success/sanic/pull/1784>`_
    Corrected changelog for docs move of MD to RST (`#1691 <https://github.com/huge-success/sanic/pull/1691>`_)

  *
    `#1803 <https://github.com/huge-success/sanic/pull/1803>`_
    Update config docs to match DEFAULT_CONFIG

  *
    `#1814 <https://github.com/huge-success/sanic/pull/1814>`_
    Update getting_started.rst

  *
    `#1821 <https://github.com/huge-success/sanic/pull/1821>`_
    Update to deployment

  *
    `#1822 <https://github.com/huge-success/sanic/pull/1822>`_
    Update docs with changes done in 20.3

  *
    `#1834 <https://github.com/huge-success/sanic/pull/1834>`_
    Order of listeners
    

Version 19.12.0
===============

Bugfixes
********

- Fix blueprint middleware application

  Currently, any blueprint middleware registered, irrespective of which blueprint was used to do so, was
  being applied to all of the routes created by the :code:`@app` and :code:`@blueprint` alike.

  As part of this change, the blueprint based middleware application is enforced based on where they are
  registered.

  - If you register a middleware via :code:`@blueprint.middleware` then it will apply only to the routes defined by the blueprint.
  - If you register a middleware via :code:`@blueprint_group.middleware` then it will apply to all blueprint based routes that are part of the group.
  - If you define a middleware via :code:`@app.middleware` then it will be applied on all available routes (`#37 <https://github.com/huge-success/sanic/issues/37>`__)
- Fix `url_for` behavior with missing SERVER_NAME

  If the `SERVER_NAME` was missing in the `app.config` entity, the `url_for` on the `request` and  `app` were failing
  due to an `AttributeError`. This fix makes the availability of `SERVER_NAME` on our `app.config` an optional behavior. (`#1707 <https://github.com/huge-success/sanic/issues/1707>`__)


Improved Documentation
**********************

- Move docs from MD to RST

  Moved all docs from markdown to restructured text like the rest of the docs to unify the scheme and make it easier in
  the future to update documentation. (`#1691 <https://github.com/huge-success/sanic/issues/1691>`__)
- Fix documentation for `get` and `getlist` of the `request.args`

  Add additional example for showing the usage of `getlist` and fix the documentation string for `request.args` behavior (`#1704 <https://github.com/huge-success/sanic/issues/1704>`__)


Version 19.6.3
==============

Features
********

- Enable Towncrier Support

  As part of this feature, `towncrier` is being introduced as a mechanism to partially  automate the process
  of generating and managing change logs as part of each of pull requests. (`#1631 <https://github.com/huge-success/sanic/issues/1631>`__)


Improved Documentation
**********************

- Documentation infrastructure changes

  - Enable having a single common `CHANGELOG` file for both GitHub page and documentation
  - Fix Sphinix deprecation warnings
  - Fix documentation warnings due to invalid `rst` indentation
  - Enable common contribution guidelines file across GitHub and documentation via `CONTRIBUTING.rst` (`#1631 <https://github.com/huge-success/sanic/issues/1631>`__)


Version 19.6.2
==============

Features
********

  * 
    `#1562 <https://github.com/huge-success/sanic/pull/1562>`_
    Remove ``aiohttp`` dependencey and create new ``SanicTestClient`` based upon
    `requests-async <https://github.com/encode/requests-async>`_

  * 
    `#1475 <https://github.com/huge-success/sanic/pull/1475>`_
    Added ASGI support (Beta)

  * 
    `#1436 <https://github.com/huge-success/sanic/pull/1436>`_
    Add Configure support from object string


Bugfixes
********

  * 
    `#1587 <https://github.com/huge-success/sanic/pull/1587>`_
    Add missing handle for Expect header.

  * 
    `#1560 <https://github.com/huge-success/sanic/pull/1560>`_
    Allow to disable Transfer-Encoding: chunked.

  * 
    `#1558 <https://github.com/huge-success/sanic/pull/1558>`_
    Fix graceful shutdown.

  * 
    `#1594 <https://github.com/huge-success/sanic/pull/1594>`_
    Strict Slashes behavior fix

Deprecations and Removals
*************************

  *
    `#1544 <https://github.com/huge-success/sanic/pull/1544>`_
    Drop dependency on distutil

  * 
    `#1562 <https://github.com/huge-success/sanic/pull/1562>`_
    Drop support for Python 3.5

  * 
    `#1568 <https://github.com/huge-success/sanic/pull/1568>`_
    Deprecate route removal.

.. warning::
    Sanic will not support Python 3.5 from version 19.6 and forward. However,
    version 18.12LTS will have its support period extended thru December 2020, and
    therefore passing Python's official support version 3.5, which is set to expire
    in September 2020.


Version 19.3
============

Features
********

  * 
    `#1497 <https://github.com/huge-success/sanic/pull/1497>`_
    Add support for zero-length and RFC 5987 encoded filename for
    multipart/form-data requests.

  * 
    `#1484 <https://github.com/huge-success/sanic/pull/1484>`_
    The type of ``expires`` attribute of ``sanic.cookies.Cookie`` is now
    enforced to be of type ``datetime``.

  * 
    `#1482 <https://github.com/huge-success/sanic/pull/1482>`_
    Add support for the ``stream`` parameter of ``sanic.Sanic.add_route()``
    available to ``sanic.Blueprint.add_route()``.

  * 
    `#1481 <https://github.com/huge-success/sanic/pull/1481>`_
    Accept negative values for route parameters with type ``int`` or ``number``.

  * 
    `#1476 <https://github.com/huge-success/sanic/pull/1476>`_
    Deprecated the use of ``sanic.request.Request.raw_args`` - it has a
    fundamental flaw in which is drops repeated query string parameters.
    Added ``sanic.request.Request.query_args`` as a replacement for the
    original use-case.

  * 
    `#1472 <https://github.com/huge-success/sanic/pull/1472>`_
    Remove an unwanted ``None`` check in Request class ``repr`` implementation.
    This changes the default ``repr`` of a Request from ``<Request>`` to
    ``<Request: None />``

  * 
    `#1470 <https://github.com/huge-success/sanic/pull/1470>`_
    Added 2 new parameters to ``sanic.app.Sanic.create_server``\ :


    * ``return_asyncio_server`` - whether to return an asyncio.Server.
    * ``asyncio_server_kwargs`` - kwargs to pass to ``loop.create_server`` for
      the event loop that sanic is using.

    This is a breaking change.

  * 
    `#1499 <https://github.com/huge-success/sanic/pull/1499>`_
    Added a set of test cases that test and benchmark route resolution.

  * 
    `#1457 <https://github.com/huge-success/sanic/pull/1457>`_
    The type of the ``"max-age"`` value in a ``sanic.cookies.Cookie`` is now
    enforced to be an integer. Non-integer values are replaced with ``0``.

  * 
    `#1445 <https://github.com/huge-success/sanic/pull/1445>`_
    Added the ``endpoint`` attribute to an incoming ``request``\ , containing the
    name of the handler function.

  * 
    `#1423 <https://github.com/huge-success/sanic/pull/1423>`_
    Improved request streaming. ``request.stream`` is now a bounded-size buffer
    instead of an unbounded queue. Callers must now call
    ``await request.stream.read()`` instead of ``await request.stream.get()``
    to read each portion of the body.

    This is a breaking change.

Bugfixes
********


  * 
    `#1502 <https://github.com/huge-success/sanic/pull/1502>`_
    Sanic was prefetching ``time.time()`` and updating it once per second to
    avoid excessive ``time.time()`` calls. The implementation was observed to
    cause memory leaks in some cases. The benefit of the prefetch appeared
    to negligible, so this has been removed. Fixes
    `#1500 <https://github.com/huge-success/sanic/pull/1500>`_

  * 
    `#1501 <https://github.com/huge-success/sanic/pull/1501>`_
    Fix a bug in the auto-reloader when the process was launched as a module
    i.e. ``python -m init0.mod1`` where the sanic server is started
    in ``init0/mod1.py`` with ``debug`` enabled and imports another module in
    ``init0``.

  * 
    `#1376 <https://github.com/huge-success/sanic/pull/1376>`_
    Allow sanic test client to bind to a random port by specifying
    ``port=None`` when constructing a ``SanicTestClient``

  * 
    `#1399 <https://github.com/huge-success/sanic/pull/1399>`_
    Added the ability to specify middleware on a blueprint group, so that all
    routes produced from the blueprints in the group have the middleware
    applied.

  * 
    `#1442 <https://github.com/huge-success/sanic/pull/1442>`_
    Allow the the use the ``SANIC_ACCESS_LOG`` environment variable to
    enable/disable the access log when not explicitly passed to ``app.run()``.
    This allows the access log to be disabled for example when running via
    gunicorn.

Developer infrastructure
************************

  * `#1529 <https://github.com/huge-success/sanic/pull/1529>`_ Update project PyPI credentials
  * `#1515 <https://github.com/huge-success/sanic/pull/1515>`_ fix linter issue causing travis build failures (fix #1514)
  * `#1490 <https://github.com/huge-success/sanic/pull/1490>`_ Fix python version in doc build
  * `#1478 <https://github.com/huge-success/sanic/pull/1478>`_ Upgrade setuptools version and use native docutils in doc build
  * `#1464 <https://github.com/huge-success/sanic/pull/1464>`_ Upgrade pytest, and fix caplog unit tests

Improved Documentation
**********************

  * `#1516 <https://github.com/huge-success/sanic/pull/1516>`_ Fix typo at the exception documentation
  * `#1510 <https://github.com/huge-success/sanic/pull/1510>`_ fix typo in Asyncio example
  * `#1486 <https://github.com/huge-success/sanic/pull/1486>`_ Documentation typo
  * `#1477 <https://github.com/huge-success/sanic/pull/1477>`_ Fix grammar in README.md
  * `#1489 <https://github.com/huge-success/sanic/pull/1489>`_ Added "databases" to the extensions list
  * `#1483 <https://github.com/huge-success/sanic/pull/1483>`_ Add sanic-zipkin to extensions list
  * `#1487 <https://github.com/huge-success/sanic/pull/1487>`_ Removed link to deleted repo, Sanic-OAuth, from the extensions list
  * `#1460 <https://github.com/huge-success/sanic/pull/1460>`_ 18.12 changelog
  * `#1449 <https://github.com/huge-success/sanic/pull/1449>`_ Add example of amending request object
  * `#1446 <https://github.com/huge-success/sanic/pull/1446>`_ Update README
  * `#1444 <https://github.com/huge-success/sanic/pull/1444>`_ Update README
  * `#1443 <https://github.com/huge-success/sanic/pull/1443>`_ Update README, including new logo
  * `#1440 <https://github.com/huge-success/sanic/pull/1440>`_ fix minor type and pip install instruction mismatch
  * `#1424 <https://github.com/huge-success/sanic/pull/1424>`_ Documentation Enhancements

Note: 19.3.0 was skipped for packagement purposes and not released on PyPI

Version 18.12
=============

18.12.0
*******

* 
  Changes:


  * Improved codebase test coverage from 81% to 91%.
  * Added stream_large_files and host examples in static_file document
  * Added methods to append and finish body content on Request (#1379)
  * Integrated with .appveyor.yml for windows ci support
  * Added documentation for AF_INET6 and AF_UNIX socket usage
  * Adopt black/isort for codestyle
  * Cancel task when connection_lost
  * Simplify request ip and port retrieval logic
  * Handle config error in load config file.
  * Integrate with codecov for CI
  * Add missed documentation for config section.
  * Deprecate Handler.log
  * Pinned httptools requirement to version 0.0.10+

* 
  Fixes:


  * Fix ``remove_entity_headers`` helper function (#1415)
  * Fix TypeError when use Blueprint.group() to group blueprint with default url_prefix, Use os.path.normpath to avoid invalid url_prefix like api//v1
    f8a6af1 Rename the ``http`` module to ``helpers`` to prevent conflicts with the built-in Python http library (fixes #1323)
  * Fix unittests on windows
  * Fix Namespacing of sanic logger
  * Fix missing quotes in decorator example
  * Fix redirect with quoted param
  * Fix doc for latest blueprint code
  * Fix build of latex documentation relating to markdown lists
  * Fix loop exception handling in app.py
  * Fix content length mismatch in windows and other platform
  * Fix Range header handling for static files (#1402)
  * Fix the logger and make it work (#1397)
  * Fix type pikcle->pickle in multiprocessing test
  * Fix pickling blueprints Change the string passed in the "name" section of the namedtuples in Blueprint to match the name of the Blueprint module attribute name. This allows blueprints to be pickled and unpickled, without errors, which is a requirment of running Sanic in multiprocessing mode in Windows. Added a test for pickling and unpickling blueprints Added a test for pickling and unpickling sanic itself Added a test for enabling multiprocessing on an app with a blueprint (only useful to catch this bug if the tests are run on Windows).
  * Fix document for logging

Version 0.8
===========

0.8.3
*****

* Changes:

  * Ownership changed to org 'huge-success'

0.8.0
*****

* Changes:


  * Add Server-Sent Events extension (Innokenty Lebedev)
  * Graceful handling of request_handler_task cancellation (Ashley Sommer)
  * Sanitize URL before redirection (aveao)
  * Add url_bytes to request (johndoe46)
  * py37 support for travisci (yunstanford)
  * Auto reloader support for OSX (garyo)
  * Add UUID route support (Volodymyr Maksymiv)
  * Add pausable response streams (Ashley Sommer)
  * Add weakref to request slots (vopankov)
  * remove ubuntu 12.04 from test fixture due to deprecation (yunstanford)
  * Allow streaming handlers in add_route (kinware)
  * use travis_retry for tox (Raphael Deem)
  * update aiohttp version for test client (yunstanford)
  * add redirect import for clarity (yingshaoxo)
  * Update HTTP Entity headers (Arnulfo Solís)
  * Add register_listener method (Stephan Fitzpatrick)
  * Remove uvloop/ujson dependencies for Windows (abuckenheimer)
  * Content-length header on 204/304 responses (Arnulfo Solís)
  * Extend WebSocketProtocol arguments and add docs (Bob Olde Hampsink, yunstanford)
  * Update development status from pre-alpha to beta (Maksim Anisenkov)
  * KeepAlive Timout log level changed to debug (Arnulfo Solís)
  * Pin pytest to 3.3.2 because of pytest-dev/pytest#3170 (Maksim Aniskenov)
  * Install Python 3.5 and 3.6 on docker container for tests (Shahin Azad)
  * Add support for blueprint groups and nesting (Elias Tarhini)
  * Remove uvloop for windows setup (Aleksandr Kurlov)
  * Auto Reload (Yaser Amari)
  * Documentation updates/fixups (multiple contributors)

* Fixes:


  * Fix: auto_reload in Linux (Ashley Sommer)
  * Fix: broken tests for aiohttp >= 3.3.0 (Ashley Sommer)
  * Fix: disable auto_reload by default on windows (abuckenheimer)
  * Fix (1143): Turn off access log with gunicorn (hqy)
  * Fix (1268): Support status code for file response (Cosmo Borsky)
  * Fix (1266): Add content_type flag to Sanic.static (Cosmo Borsky)
  * Fix: subprotocols parameter missing from add_websocket_route (ciscorn)
  * Fix (1242): Responses for CI header (yunstanford)
  * Fix (1237): add version constraint for websockets (yunstanford)
  * Fix (1231): memory leak - always release resource (Phillip Xu)
  * Fix (1221): make request truthy if transport exists (Raphael Deem)
  * Fix failing tests for aiohttp>=3.1.0 (Ashley Sommer)
  * Fix try_everything examples (PyManiacGR, kot83)
  * Fix (1158): default to auto_reload in debug mode (Raphael Deem)
  * Fix (1136): ErrorHandler.response handler call too restrictive (Julien Castiaux)
  * Fix: raw requires bytes-like object (cloudship)
  * Fix (1120): passing a list in to a route decorator's host arg (Timothy Ebiuwhe)
  * Fix: Bug in multipart/form-data parser (DirkGuijt)
  * Fix: Exception for missing parameter when value is null (NyanKiyoshi)
  * Fix: Parameter check (Howie Hu)
  * Fix (1089): Routing issue with named parameters and different methods (yunstanford)
  * Fix (1085): Signal handling in multi-worker mode (yunstanford)
  * Fix: single quote in readme.rst (Cosven)
  * Fix: method typos (Dmitry Dygalo)
  * Fix: log_response correct output for ip and port (Wibowo Arindrarto)
  * Fix (1042): Exception Handling (Raphael Deem)
  * Fix: Chinese URIs (Howie Hu)
  * Fix (1079): timeout bug when self.transport is None (Raphael Deem)
  * Fix (1074): fix strict_slashes when route has slash (Raphael Deem)
  * Fix (1050): add samesite cookie to cookie keys (Raphael Deem)
  * Fix (1065): allow add_task after server starts (Raphael Deem)
  * Fix (1061): double quotes in unauthorized exception (Raphael Deem)
  * Fix (1062): inject the app in add_task method (Raphael Deem)
  * Fix: update environment.yml for readthedocs (Eli Uriegas)
  * Fix: Cancel request task when response timeout is triggered (Jeong YunWon)
  * Fix (1052): Method not allowed response for RFC7231 compliance (Raphael Deem)
  * Fix: IPv6 Address and Socket Data Format (Dan Palmer)

Note: Changelog was unmaintained between 0.1 and 0.7

Version 0.1
===========


0.1.7
*****

  * Reversed static url and directory arguments to meet spec

0.1.6
*****

  * Static files
  * Lazy Cookie Loading

0.1.5
*****

  * Cookies
  * Blueprint listeners and ordering
  * Faster Router
  * Fix: Incomplete file reads on medium+ sized post requests
  * Breaking: after_start and before_stop now pass sanic as their first argument

0.1.4
*****

  * Multiprocessing

0.1.3
*****

  * Blueprint support
  * Faster Response processing

0.1.1 - 0.1.2
*************

  * Struggling to update pypi via CI

0.1.0
*****

  * Released to public
