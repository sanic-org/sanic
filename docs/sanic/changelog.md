Version 19.6
------------
19.6.0
  - Changes:
    - Remove `aiohttp` dependencey and create new `SanicTestClient` based upon
    [`requests-async`](https://github.com/encode/requests-async).

  - Deprecation:
    - Support for Python 3.5

Note: Sanic will not support Python 3.5 from version 19.6 and forward. However,
version 18.12LTS will have its support period extended thru December 2020, and
therefore passing Python's official support version 3.5, which is set to expire
in September 2020.

Version 19.3
-------------
19.3.1
  - Changes:
    - [#1497](https://github.com/huge-success/sanic/pull/1497)
      Add support for zero-length and RFC 5987 encoded filename for
      multipart/form-data requests.

    - [#1484](https://github.com/huge-success/sanic/pull/1484)
      The type of `expires` attribute of `sanic.cookies.Cookie` is now
      enforced to be of type `datetime`.

    - [#1482](https://github.com/huge-success/sanic/pull/1482)
      Add support for the `stream` parameter of `sanic.Sanic.add_route()`
      available to `sanic.Blueprint.add_route()`.

    - [#1481](https://github.com/huge-success/sanic/pull/1481)
      Accept negative values for route parameters with type `int` or `number`.

    - [#1476](https://github.com/huge-success/sanic/pull/1476)
      Deprecated the use of `sanic.request.Request.raw_args` - it has a
      fundamental flaw in which is drops repeated query string parameters.
      Added `sanic.request.Request.query_args` as a replacement for the
      original use-case.

    - [#1472](https://github.com/huge-success/sanic/pull/1472)
      Remove an unwanted `None` check in Request class `repr` implementation.
      This changes the default `repr` of a Request from `<Request>` to
      `<Request: None />`

    - [#1470](https://github.com/huge-success/sanic/pull/1470)
      Added 2 new parameters to `sanic.app.Sanic.create_server`:
      - `return_asyncio_server` - whether to return an asyncio.Server.
      - `asyncio_server_kwargs` - kwargs to pass to `loop.create_server` for
        the event loop that sanic is using.

      This is a breaking change.

    - [#1499](https://github.com/huge-success/sanic/pull/1499)
      Added a set of test cases that test and benchmark route resolution.

    - [#1457](https://github.com/huge-success/sanic/pull/1457)
      The type of the `"max-age"` value in a `sanic.cookies.Cookie` is now
      enforced to be an integer. Non-integer values are replaced with `0`.

    - [#1445](https://github.com/huge-success/sanic/pull/1445)
      Added the `endpoint` attribute to an incoming `request`, containing the
      name of the handler function.

    - [#1423](https://github.com/huge-success/sanic/pull/1423)
      Improved request streaming. `request.stream` is now a bounded-size buffer
      instead of an unbounded queue. Callers must now call
      `await request.stream.read()` instead of `await request.stream.get()`
      to read each portion of the body.

      This is a breaking change.

  - Fixes:
    - [#1502](https://github.com/huge-success/sanic/pull/1502)
      Sanic was prefetching `time.time()` and updating it once per second to
      avoid excessive `time.time()` calls. The implementation was observed to
      cause memory leaks in some cases. The benefit of the prefetch appeared
      to negligible, so this has been removed. Fixes
      [#1500](https://github.com/huge-success/sanic/pull/1500)

    - [#1501](https://github.com/huge-success/sanic/pull/1501)
      Fix a bug in the auto-reloader when the process was launched as a module
      i.e. `python -m init0.mod1` where the sanic server is started
      in `init0/mod1.py` with `debug` enabled and imports another module in
      `init0`.

    - [#1376](https://github.com/huge-success/sanic/pull/1376)
      Allow sanic test client to bind to a random port by specifying
      `port=None` when constructing a `SanicTestClient`

    - [#1399](https://github.com/huge-success/sanic/pull/1399)
      Added the ability to specify middleware on a blueprint group, so that all
      routes produced from the blueprints in the group have the middleware
      applied.

    - [#1442](https://github.com/huge-success/sanic/pull/1442)
      Allow the the use the `SANIC_ACCESS_LOG` environment variable to
      enable/disable the access log when not explicitly passed to `app.run()`.
      This allows the access log to be disabled for example when running via
      gunicorn.

  - Developer infrastructure:
    - [#1529](https://github.com/huge-success/sanic/pull/1529) Update project PyPI credentials
    - [#1515](https://github.com/huge-success/sanic/pull/1515) fix linter issue causing travis build failures (fix #1514)
    - [#1490](https://github.com/huge-success/sanic/pull/1490) Fix python version in doc build
    - [#1478](https://github.com/huge-success/sanic/pull/1478) Upgrade setuptools version and use native docutils in doc build
    - [#1464](https://github.com/huge-success/sanic/pull/1464) Upgrade pytest, and fix caplog unit tests

  - Typos and Documentation:
    - [#1516](https://github.com/huge-success/sanic/pull/1516) Fix typo at the exception documentation
    - [#1510](https://github.com/huge-success/sanic/pull/1510) fix typo in Asyncio example
    - [#1486](https://github.com/huge-success/sanic/pull/1486) Documentation typo
    - [#1477](https://github.com/huge-success/sanic/pull/1477) Fix grammar in README.md
    - [#1489](https://github.com/huge-success/sanic/pull/1489) Added "databases" to the extensions list
    - [#1483](https://github.com/huge-success/sanic/pull/1483) Add sanic-zipkin to extensions list
    - [#1487](https://github.com/huge-success/sanic/pull/1487) Removed link to deleted repo, Sanic-OAuth, from the extensions list
    - [#1460](https://github.com/huge-success/sanic/pull/1460) 18.12 changelog
    - [#1449](https://github.com/huge-success/sanic/pull/1449) Add example of amending request object
    - [#1446](https://github.com/huge-success/sanic/pull/1446) Update README
    - [#1444](https://github.com/huge-success/sanic/pull/1444) Update README
    - [#1443](https://github.com/huge-success/sanic/pull/1443) Update README, including new logo
    - [#1440](https://github.com/huge-success/sanic/pull/1440) fix minor type and pip install instruction mismatch
    - [#1424](https://github.com/huge-success/sanic/pull/1424) Documentation Enhancements

Note: 19.3.0 was skipped for packagement purposes and not released on PyPI

Version 18.12
-------------
18.12.0
  - Changes:
    - Improved codebase test coverage from 81% to 91%.
    - Added stream_large_files and host examples in static_file document
    - Added methods to append and finish body content on Request (#1379)
    - Integrated with .appveyor.yml for windows ci support
    - Added documentation for AF_INET6 and AF_UNIX socket usage
    - Adopt black/isort for codestyle
    - Cancel task when connection_lost
    - Simplify request ip and port retrieval logic
    - Handle config error in load config file.
    - Integrate with codecov for CI
    - Add missed documentation for config section.
    - Deprecate Handler.log
    - Pinned httptools requirement to version 0.0.10+

  - Fixes:
    - Fix `remove_entity_headers` helper function (#1415)
    - Fix TypeError when use Blueprint.group() to group blueprint with default url_prefix, Use os.path.normpath to avoid invalid url_prefix like api//v1
    f8a6af1 Rename the `http` module to `helpers` to prevent conflicts with the built-in Python http library (fixes #1323)
    - Fix unittests on windows
    - Fix Namespacing of sanic logger
    - Fix missing quotes in decorator example
    - Fix redirect with quoted param
    - Fix doc for latest blueprint code
    - Fix build of latex documentation relating to markdown lists
    - Fix loop exception handling in app.py
    - Fix content length mismatch in windows and other platform
    - Fix Range header handling for static files (#1402)
    - Fix the logger and make it work (#1397)
    - Fix type pikcle->pickle in multiprocessing test
    - Fix pickling blueprints Change the string passed in the "name" section of the namedtuples in Blueprint to match the name of the Blueprint module attribute name. This allows blueprints to be pickled and unpickled, without errors, which is a requirment of running Sanic in multiprocessing mode in Windows. Added a test for pickling and unpickling blueprints Added a test for pickling and unpickling sanic itself Added a test for enabling multiprocessing on an app with a blueprint (only useful to catch this bug if the tests are run on Windows).
    - Fix document for logging

Version 0.8
-----------
0.8.3
  - Changes:
    - Ownership changed to org 'huge-success'

0.8.0
  - Changes:
    - Add Server-Sent Events extension (Innokenty Lebedev)
    - Graceful handling of request_handler_task cancellation (Ashley Sommer)
    - Sanitize URL before redirection (aveao)
    - Add url_bytes to request (johndoe46)
    - py37 support for travisci (yunstanford)
    - Auto reloader support for OSX (garyo)
    - Add UUID route support (Volodymyr Maksymiv)
    - Add pausable response streams (Ashley Sommer)
    - Add weakref to request slots (vopankov)
    - remove ubuntu 12.04 from test fixture due to deprecation (yunstanford)
    - Allow streaming handlers in add_route (kinware)
    - use travis_retry for tox (Raphael Deem)
    - update aiohttp version for test client (yunstanford)
    - add redirect import for clarity (yingshaoxo)
    - Update HTTP Entity headers (Arnulfo Solís)
    - Add register_listener method (Stephan Fitzpatrick)
    - Remove uvloop/ujson dependencies for Windows (abuckenheimer)
    - Content-length header on 204/304 responses (Arnulfo Solís)
    - Extend WebSocketProtocol arguments and add docs (Bob Olde Hampsink, yunstanford)
    - Update development status from pre-alpha to beta (Maksim Anisenkov)
    - KeepAlive Timout log level changed to debug (Arnulfo Solís)
    - Pin pytest to 3.3.2 because of pytest-dev/pytest#3170 (Maksim Aniskenov)
    - Install Python 3.5 and 3.6 on docker container for tests (Shahin Azad)
    - Add support for blueprint groups and nesting (Elias Tarhini)
    - Remove uvloop for windows setup (Aleksandr Kurlov)
    - Auto Reload (Yaser Amari)
    - Documentation updates/fixups (multiple contributors)

  - Fixes:
    - Fix: auto_reload in Linux (Ashley Sommer)
    - Fix: broken tests for aiohttp >= 3.3.0 (Ashley Sommer)
    - Fix: disable auto_reload by default on windows (abuckenheimer)
    - Fix (1143): Turn off access log with gunicorn (hqy)
    - Fix (1268): Support status code for file response (Cosmo Borsky)
    - Fix (1266): Add content_type flag to Sanic.static (Cosmo Borsky)
    - Fix: subprotocols parameter missing from add_websocket_route (ciscorn)
    - Fix (1242): Responses for CI header (yunstanford)
    - Fix (1237): add version constraint for websockets (yunstanford)
    - Fix (1231): memory leak - always release resource (Phillip Xu)
    - Fix (1221): make request truthy if transport exists (Raphael Deem)
    - Fix failing tests for aiohttp>=3.1.0 (Ashley Sommer)
    - Fix try_everything examples (PyManiacGR, kot83)
    - Fix (1158): default to auto_reload in debug mode (Raphael Deem)
    - Fix (1136): ErrorHandler.response handler call too restrictive (Julien Castiaux)
    - Fix: raw requires bytes-like object (cloudship)
    - Fix (1120): passing a list in to a route decorator's host arg (Timothy Ebiuwhe)
    - Fix: Bug in multipart/form-data parser (DirkGuijt)
    - Fix: Exception for missing parameter when value is null (NyanKiyoshi)
    - Fix: Parameter check (Howie Hu)
    - Fix (1089): Routing issue with named parameters and different methods (yunstanford)
    - Fix (1085): Signal handling in multi-worker mode (yunstanford)
    - Fix: single quote in readme.rst (Cosven)
    - Fix: method typos (Dmitry Dygalo)
    - Fix: log_response correct output for ip and port (Wibowo Arindrarto)
    - Fix (1042): Exception Handling (Raphael Deem)
    - Fix: Chinese URIs (Howie Hu)
    - Fix (1079): timeout bug when self.transport is None (Raphael Deem)
    - Fix (1074): fix strict_slashes when route has slash (Raphael Deem)
    - Fix (1050): add samesite cookie to cookie keys (Raphael Deem)
    - Fix (1065): allow add_task after server starts (Raphael Deem)
    - Fix (1061): double quotes in unauthorized exception (Raphael Deem)
    - Fix (1062): inject the app in add_task method (Raphael Deem)
    - Fix: update environment.yml for readthedocs (Eli Uriegas)
    - Fix: Cancel request task when response timeout is triggered (Jeong YunWon)
    - Fix (1052): Method not allowed response for RFC7231 compliance (Raphael Deem)
    - Fix: IPv6 Address and Socket Data Format (Dan Palmer)

Note: Changelog was unmaintained between 0.1 and 0.7

Version 0.1
-----------
 - 0.1.7
  - Reversed static url and directory arguments to meet spec
 - 0.1.6
  - Static files
  - Lazy Cookie Loading
 - 0.1.5
  - Cookies
  - Blueprint listeners and ordering
  - Faster Router
  - Fix: Incomplete file reads on medium+ sized post requests
  - Breaking: after_start and before_stop now pass sanic as their first argument
 - 0.1.4
  - Multiprocessing
 - 0.1.3
  - Blueprint support
  - Faster Response processing
 - 0.1.1 - 0.1.2
  - Struggling to update pypi via CI
 - 0.1.0
  - Released to public
