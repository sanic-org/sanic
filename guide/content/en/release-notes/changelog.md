---
content_class: changelog
---

# Changelog

🔶 Current release  
🔷 In support LTS release

## Version 24.12.0 🔶🔷

_Current version_

### Features
- [#3019](https://github.com/sanic-org/sanic/pull/3019) Add custom commands to `sanic` CLI

### Bugfixes
- [#2992](https://github.com/sanic-org/sanic/pull/2992) Fix `mixins.startup.serve` UnboundLocalError
- [#3000](https://github.com/sanic-org/sanic/pull/3000) Fix type annocation for `JSONResponse` method for return type `bytes` allowed for `dumps` callable
- [#3009](https://github.com/sanic-org/sanic/pull/3009) Fix `SanicException.quiet` attribute handling when set to `False`
- [#3014](https://github.com/sanic-org/sanic/pull/3014) Cleanup some typing
- [#3015](https://github.com/sanic-org/sanic/pull/3015) Kill the entire process group if applicable
- [#3016](https://github.com/sanic-org/sanic/pull/3016) Fix incompatible type annotation of get method in the HTTPMethodView class

### Deprecations and Removals
- [#3020](https://github.com/sanic-org/sanic/pull/3020) Remove Python 3.8 support

### Developer infrastructure
- [#3017](https://github.com/sanic-org/sanic/pull/3017) Cleanup setup.cfg

### Improved Documentation
- [#3007](https://github.com/sanic-org/sanic/pull/3007) Fix typo in documentation for `sanic-ext`

## Version 24.6.0

### Features
- [#2838](https://github.com/sanic-org/sanic/pull/2838) Simplify request cookies `getlist`
- [#2850](https://github.com/sanic-org/sanic/pull/2850) Unix sockets can now use `pathlib.Path`
- [#2931](https://github.com/sanic-org/sanic/pull/2931) [#2958](https://github.com/sanic-org/sanic/pull/2958) Logging improvements
- [#2947](https://github.com/sanic-org/sanic/pull/2947) Make the .message field on exceptions non-empty
- [#2961](https://github.com/sanic-org/sanic/pull/2961) [#2964](https://github.com/sanic-org/sanic/pull/2964) Allow for custom name generation

### Bugfixes
- [#2919](https://github.com/sanic-org/sanic/pull/2919) Remove deprecation notice in websockets
- [#2937](https://github.com/sanic-org/sanic/pull/2937) Resolve response streaming error when in ASGI mode
- [#2959](https://github.com/sanic-org/sanic/pull/2959) Resolve Python 3.12 deprecation notic
- [#2960](https://github.com/sanic-org/sanic/pull/2960) Ensure proper intent for noisy exceptions
- [#2970](https://github.com/sanic-org/sanic/pull/2970) [#2978](https://github.com/sanic-org/sanic/pull/2978) Fix missing dependencies for 3.12
- [#2971](https://github.com/sanic-org/sanic/pull/2971) Fix middleware exceptions on Not Found routes with error in middleware
- [#2973](https://github.com/sanic-org/sanic/pull/2973) Resolve cheduling logic for `transport.close` and `transport.abort`
- [#2976](https://github.com/sanic-org/sanic/pull/2976) Fix deleting a cookie that was created with `secure=False`
- [#2979](https://github.com/sanic-org/sanic/pull/2979) Throw error on bad body length
- [#2980](https://github.com/sanic-org/sanic/pull/2980) Throw error on bad body encoding

### Deprecations and Removals
- [#2899](https://github.com/sanic-org/sanic/pull/2899) Remove erroneous line from REPL impacting environments without HTTPX
- [#2962](https://github.com/sanic-org/sanic/pull/2962) Merge entity header removal

### Developer infrastructure
- [#2882](https://github.com/sanic-org/sanic/pull/2882) [#2896](https://github.com/sanic-org/sanic/pull/2896) Apply dynamic port fixture for improving tests with port selection
- [#2887](https://github.com/sanic-org/sanic/pull/2887) Updates to docker image builds
- [#2932](https://github.com/sanic-org/sanic/pull/2932) Cleanup code base with Ruff

### Improved Documentation
- [#2924](https://github.com/sanic-org/sanic/pull/2924) Cleanup markdown on html5tagger page
- [#2930](https://github.com/sanic-org/sanic/pull/2930) Cleanup typo on Sanic Extensions README.md
- [#2934](https://github.com/sanic-org/sanic/pull/2934) Add more context to the health check documents
- [#2936](https://github.com/sanic-org/sanic/pull/2936) Improve worker manager documentation
- [#2955](https://github.com/sanic-org/sanic/pull/2955) Fixed wrong formatting in `request.md`

## Version 23.12.0 🔷

### Features
- [#2775](https://github.com/sanic-org/sanic/pull/2775) Start and restart arbitrary processes
- [#2811](https://github.com/sanic-org/sanic/pull/2811) Cleaner process management in shutdown
- [#2812](https://github.com/sanic-org/sanic/pull/2812) Suppress task cancel traceback on open websocket
- [#2822](https://github.com/sanic-org/sanic/pull/2822) Listener and signal prioritization
- [#2831](https://github.com/sanic-org/sanic/pull/2831) Reduce memory consumption
- [#2837](https://github.com/sanic-org/sanic/pull/2837) Accept bare cookies
- [#2841](https://github.com/sanic-org/sanic/pull/2841) Add `websocket.handler.<before/after/exception>` signals
- [#2805](https://github.com/sanic-org/sanic/pull/2805) Add changed files to reload trigger listeners
- [#2813](https://github.com/sanic-org/sanic/pull/2813) Allow for simple signals
- [#2827](https://github.com/sanic-org/sanic/pull/2827) Improve functionality and consistency of `Sanic.event()`
- [#2851](https://github.com/sanic-org/sanic/pull/2851) Allow range requests for a single byte
- [#2854](https://github.com/sanic-org/sanic/pull/2854) Better `Request.scheme` for websocket requests
- [#2858](https://github.com/sanic-org/sanic/pull/2858) Convert Sanic `Request` to a Websockets `Request` for handshake
- [#2859](https://github.com/sanic-org/sanic/pull/2859) Add a REPL to the `sanic` CLI
- [#2870](https://github.com/sanic-org/sanic/pull/2870) Add Python 3.12 support
- [#2875](https://github.com/sanic-org/sanic/pull/2875) Better exception on multiprocessing context conflicts

### Bugfixes
- [#2803](https://github.com/sanic-org/sanic/pull/2803) Fix MOTD display for extra data

### Developer infrastructure
- [#2796](https://github.com/sanic-org/sanic/pull/2796) Refactor unit test cases
- [#2801](https://github.com/sanic-org/sanic/pull/2801) Fix `test_fast` when there is only one CPU
- [#2807](https://github.com/sanic-org/sanic/pull/2807) Add constraint for autodocsum (lint issue in old package version)
- [#2808](https://github.com/sanic-org/sanic/pull/2808) Refactor GitHub Actions
- [#2814](https://github.com/sanic-org/sanic/pull/2814) Run CI pipeline on git push
- [#2846](https://github.com/sanic-org/sanic/pull/2846) Drop old performance tests/benchmarks
- [#2848](https://github.com/sanic-org/sanic/pull/2848) Makefile cleanup
- [#2865](https://github.com/sanic-org/sanic/pull/2865)
  [#2869](https://github.com/sanic-org/sanic/pull/2869)
  [#2872](https://github.com/sanic-org/sanic/pull/2872)
  [#2879](https://github.com/sanic-org/sanic/pull/2879)
  Add ruff to toolchain
- [#2866](https://github.com/sanic-org/sanic/pull/2866) Fix the alt svc test to run locally with explicit buffer nbytes
- [#2877](https://github.com/sanic-org/sanic/pull/2877) Use Python's trusted publisher in deployments
- [#2882](https://github.com/sanic-org/sanic/pull/2882) Introduce dynamic port fixture in targeted locations in the test suite

### Improved Documentation
- [#2781](https://github.com/sanic-org/sanic/pull/2781)
  [#2821](https://github.com/sanic-org/sanic/pull/2821)
  [#2861](https://github.com/sanic-org/sanic/pull/2861)
  [#2863](https://github.com/sanic-org/sanic/pull/2863)
  Conversion of User Guide to the SHH (Sanic, html5tagger, HTMX) stack
- [#2810](https://github.com/sanic-org/sanic/pull/2810) Update README
- [#2855](https://github.com/sanic-org/sanic/pull/2855) Edit Discord badge
- [#2864](https://github.com/sanic-org/sanic/pull/2864) Adjust documentation for using state properties within http/https redirection document


## Version 23.9.0

_Due to circumstances at the time, v.23.9 was skipped._


## Version 23.6.0

### Features
- [#2670](https://github.com/sanic-org/sanic/pull/2670) Increase `KEEP_ALIVE_TIMEOUT` default to 120 seconds
- [#2716](https://github.com/sanic-org/sanic/pull/2716) Adding allow route overwrite option in blueprint
- [#2724](https://github.com/sanic-org/sanic/pull/2724) and [#2792](https://github.com/sanic-org/sanic/pull/2792) Add a new exception signal for ALL exceptions raised anywhere in application
- [#2727](https://github.com/sanic-org/sanic/pull/2727) Add name prefixing to BP groups
- [#2754](https://github.com/sanic-org/sanic/pull/2754) Update request type on middleware types
- [#2770](https://github.com/sanic-org/sanic/pull/2770) Better exception message on startup time application induced import error
- [#2776](https://github.com/sanic-org/sanic/pull/2776) Set multiprocessing start method early
- [#2785](https://github.com/sanic-org/sanic/pull/2785) Add custom typing to config and ctx objects
- [#2790](https://github.com/sanic-org/sanic/pull/2790) Add `request.client_ip`

### Bugfixes
- [#2728](https://github.com/sanic-org/sanic/pull/2728) Fix traversals for intended results
- [#2729](https://github.com/sanic-org/sanic/pull/2729) Handle case when headers argument of ResponseStream constructor is None
- [#2737](https://github.com/sanic-org/sanic/pull/2737) Fix type annotation for `JSONREsponse` default content type
- [#2740](https://github.com/sanic-org/sanic/pull/2740) Use Sanic's serializer for JSON responses in the Inspector
- [#2760](https://github.com/sanic-org/sanic/pull/2760) Support for `Request.get_current` in ASGI mode
- [#2773](https://github.com/sanic-org/sanic/pull/2773) Alow Blueprint routes to explicitly define error_format
- [#2774](https://github.com/sanic-org/sanic/pull/2774) Resolve headers on different renderers
- [#2782](https://github.com/sanic-org/sanic/pull/2782) Resolve pypy compatibility issues

### Deprecations and Removals
- [#2777](https://github.com/sanic-org/sanic/pull/2777) Remove Python 3.7 support

### Developer infrastructure
- [#2766](https://github.com/sanic-org/sanic/pull/2766) Unpin setuptools version
- [#2779](https://github.com/sanic-org/sanic/pull/2779) Run keep alive tests in loop to get available port

### Improved Documentation
- [#2741](https://github.com/sanic-org/sanic/pull/2741) Better documentation examples about running Sanic
From that list, the items to highlight in the release notes:


## Version 23.3.0

### Features
- [#2545](https://github.com/sanic-org/sanic/pull/2545) Standardize init of exceptions for more consistent control of HTTP responses using exceptions
- [#2606](https://github.com/sanic-org/sanic/pull/2606) Decode headers as UTF-8 also in ASGI
- [#2646](https://github.com/sanic-org/sanic/pull/2646) Separate ASGI request and lifespan callables
- [#2659](https://github.com/sanic-org/sanic/pull/2659) Use ``FALLBACK_ERROR_FORMAT`` for handlers that return ``empty()``
- [#2662](https://github.com/sanic-org/sanic/pull/2662) Add basic file browser (HTML page) and auto-index serving
- [#2667](https://github.com/sanic-org/sanic/pull/2667) Nicer traceback formatting (HTML page)
- [#2668](https://github.com/sanic-org/sanic/pull/2668) Smarter error page rendering format selection; more reliant upon header and "common sense" defaults
- [#2680](https://github.com/sanic-org/sanic/pull/2680) Check the status of socket before shutting down with ``SHUT_RDWR``
- [#2687](https://github.com/sanic-org/sanic/pull/2687) Refresh ``Request.accept`` functionality to be more performant and spec-compliant
- [#2696](https://github.com/sanic-org/sanic/pull/2696) Add header accessors as properties
    ```
    Example-Field: Foo, Bar
    Example-Field: Baz
    ```
    ```python
    request.headers.example_field == "Foo, Bar,Baz"
    ```
- [#2700](https://github.com/sanic-org/sanic/pull/2700) Simpler CLI targets

    ```sh
    $ sanic path.to.module:app          # global app instance
    $ sanic path.to.module:create_app   # factory pattern
    $ sanic ./path/to/directory/        # simple serve
    ```
- [#2701](https://github.com/sanic-org/sanic/pull/2701) API to define a number of workers in managed processes
- [#2704](https://github.com/sanic-org/sanic/pull/2704) Add convenience for dynamic changes to routing
- [#2706](https://github.com/sanic-org/sanic/pull/2706) Add convenience methods for cookie creation and deletion
    
    ```python
    response = text("...")
    response.add_cookie("test", "It worked!", domain=".yummy-yummy-cookie.com")
    ```
- [#2707](https://github.com/sanic-org/sanic/pull/2707) Simplified ``parse_content_header`` escaping to be RFC-compliant and remove outdated FF hack
- [#2710](https://github.com/sanic-org/sanic/pull/2710) Stricter charset handling and escaping of request URLs
- [#2711](https://github.com/sanic-org/sanic/pull/2711) Consume body on ``DELETE`` by default
- [#2719](https://github.com/sanic-org/sanic/pull/2719) Allow ``password`` to be passed to TLS context
- [#2720](https://github.com/sanic-org/sanic/pull/2720) Skip middleware on ``RequestCancelled``
- [#2721](https://github.com/sanic-org/sanic/pull/2721) Change access logging format to ``%s``
- [#2722](https://github.com/sanic-org/sanic/pull/2722) Add ``CertLoader`` as application option for directly controlling ``SSLContext`` objects
- [#2725](https://github.com/sanic-org/sanic/pull/2725) Worker sync state tolerance on race condition

### Bugfixes
- [#2651](https://github.com/sanic-org/sanic/pull/2651) ASGI websocket to pass thru bytes as is
- [#2697](https://github.com/sanic-org/sanic/pull/2697) Fix comparison between datetime aware and naive in ``file`` when using ``If-Modified-Since``

### Deprecations and Removals
- [#2666](https://github.com/sanic-org/sanic/pull/2666) Remove deprecated ``__blueprintname__`` property

### Improved Documentation
- [#2712](https://github.com/sanic-org/sanic/pull/2712) Improved example using ``'https'`` to create the redirect


## Version 22.12.0

_Current LTS version_

### Features

- [#2569](https://github.com/sanic-org/sanic/pull/2569) Add `JSONResponse` class with some convenient methods when updating a response object
- [#2598](https://github.com/sanic-org/sanic/pull/2598) Change `uvloop` requirement to `>=0.15.0`
- [#2609](https://github.com/sanic-org/sanic/pull/2609) Add compatibility with `websockets` v11.0
- [#2610](https://github.com/sanic-org/sanic/pull/2610) Kill server early on worker error
    - Raise deadlock timeout to 30s
- [#2617](https://github.com/sanic-org/sanic/pull/2617) Scale number of running server workers
- [#2621](https://github.com/sanic-org/sanic/pull/2621) [#2634](https://github.com/sanic-org/sanic/pull/2634) Send `SIGKILL` on subsequent `ctrl+c` to force worker exit
- [#2622](https://github.com/sanic-org/sanic/pull/2622) Add API to restart all workers from the multiplexer
- [#2624](https://github.com/sanic-org/sanic/pull/2624) Default to `spawn` for all subprocesses unless specifically set:
    ```python
    from sanic import Sanic
    
    Sanic.start_method = "fork"
    ```
- [#2625](https://github.com/sanic-org/sanic/pull/2625) Filename normalisation of form-data/multipart file uploads
- [#2626](https://github.com/sanic-org/sanic/pull/2626) Move to HTTP Inspector:
    - Remote access to inspect running Sanic instances
    - TLS support for encrypted calls to Inspector
    - Authentication to Inspector with API key
    - Ability to extend Inspector with custom commands
- [#2632](https://github.com/sanic-org/sanic/pull/2632) Control order of restart operations
- [#2633](https://github.com/sanic-org/sanic/pull/2633) Move reload interval to class variable
- [#2636](https://github.com/sanic-org/sanic/pull/2636) Add `priority` to `register_middleware` method
- [#2639](https://github.com/sanic-org/sanic/pull/2639) Add `unquote` to `add_route` method
- [#2640](https://github.com/sanic-org/sanic/pull/2640) ASGI websockets to receive `text` or `bytes`


### Bugfixes

- [#2607](https://github.com/sanic-org/sanic/pull/2607) Force socket shutdown before close to allow rebinding
- [#2590](https://github.com/sanic-org/sanic/pull/2590) Use actual `StrEnum` in Python 3.11+
- [#2615](https://github.com/sanic-org/sanic/pull/2615) Ensure middleware executes only once per request timeout
- [#2627](https://github.com/sanic-org/sanic/pull/2627) Crash ASGI application on lifespan failure
- [#2635](https://github.com/sanic-org/sanic/pull/2635) Resolve error with low-level server creation on Windows


### Deprecations and Removals

- [#2608](https://github.com/sanic-org/sanic/pull/2608) [#2630](https://github.com/sanic-org/sanic/pull/2630) Signal conditions and triggers saved on `signal.extra` 
- [#2626](https://github.com/sanic-org/sanic/pull/2626) Move to HTTP Inspector
    - 🚨 *BREAKING CHANGE*: Moves the Inspector to a Sanic app from a simple TCP socket with a custom protocol
    - *DEPRECATE*: The `--inspect*` commands have been deprecated in favor of `inspect ...` commands
- [#2628](https://github.com/sanic-org/sanic/pull/2628) Replace deprecated `distutils.strtobool`


### Developer infrastructure

- [#2612](https://github.com/sanic-org/sanic/pull/2612) Add CI testing for Python 3.11


## Version 22.9.1

### Features

- [#2585](https://github.com/sanic-org/sanic/pull/2585) Improved error message when no applications have been registered


### Bugfixes

- [#2578](https://github.com/sanic-org/sanic/pull/2578) Add certificate loader for in process certificate creation
- [#2591](https://github.com/sanic-org/sanic/pull/2591) Do not use sentinel identity for `spawn` compatibility
- [#2592](https://github.com/sanic-org/sanic/pull/2592) Fix properties in nested blueprint groups
- [#2595](https://github.com/sanic-org/sanic/pull/2595) Introduce sleep interval on new worker reloader


### Deprecations and Removals


### Developer infrastructure

- [#2588](https://github.com/sanic-org/sanic/pull/2588) Markdown templates on issue forms


### Improved Documentation

- [#2556](https://github.com/sanic-org/sanic/pull/2556) v22.9 documentation
- [#2582](https://github.com/sanic-org/sanic/pull/2582) Cleanup documentation on Windows support


## Version 22.9.0

### Features

- [#2445](https://github.com/sanic-org/sanic/pull/2445) Add custom loads function 
- [#2490](https://github.com/sanic-org/sanic/pull/2490) Make `WebsocketImplProtocol` async iterable
- [#2499](https://github.com/sanic-org/sanic/pull/2499) Sanic Server WorkerManager refactor
- [#2506](https://github.com/sanic-org/sanic/pull/2506) Use `pathlib` for path resolution (for static file serving)
- [#2508](https://github.com/sanic-org/sanic/pull/2508) Use `path.parts` instead of `match` (for static file serving)
- [#2513](https://github.com/sanic-org/sanic/pull/2513) Better request cancel handling
- [#2516](https://github.com/sanic-org/sanic/pull/2516) Add request properties for HTTP method info:
    - `request.is_safe`
    - `request.is_idempotent`
    - `request.is_cacheable`
    - *See* [MDN docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods) *for more information about when these apply*
- [#2522](https://github.com/sanic-org/sanic/pull/2522) Always show server location in ASGI
- [#2526](https://github.com/sanic-org/sanic/pull/2526) Cache control support for static files for returning 304 when appropriate
- [#2533](https://github.com/sanic-org/sanic/pull/2533) Refactor `_static_request_handler`
- [#2540](https://github.com/sanic-org/sanic/pull/2540) Add signals before and after handler execution
    - `http.handler.before`
    - `http.handler.after`
- [#2542](https://github.com/sanic-org/sanic/pull/2542) Add *[redacted]* to CLI :)
- [#2546](https://github.com/sanic-org/sanic/pull/2546) Add deprecation warning filter
- [#2550](https://github.com/sanic-org/sanic/pull/2550) Middleware priority and performance enhancements

### Bugfixes

- [#2495](https://github.com/sanic-org/sanic/pull/2495) Prevent directory traversion with static files
- [#2515](https://github.com/sanic-org/sanic/pull/2515) Do not apply double slash to paths in certain static dirs in Blueprints

### Deprecations and Removals

- [#2525](https://github.com/sanic-org/sanic/pull/2525) Warn on duplicate route names, will be prevented outright in v23.3
- [#2537](https://github.com/sanic-org/sanic/pull/2537) Raise warning and deprecation notice on duplicate exceptions, will be prevented outright in v23.3

### Developer infrastructure

- [#2504](https://github.com/sanic-org/sanic/pull/2504) Cleanup test suite
- [#2505](https://github.com/sanic-org/sanic/pull/2505) Replace Unsupported Python Version Number from the Contributing Doc
- [#2530](https://github.com/sanic-org/sanic/pull/2530) Do not include tests folder in installed package resolver

### Improved Documentation

- [#2502](https://github.com/sanic-org/sanic/pull/2502) Fix a few typos
- [#2517](https://github.com/sanic-org/sanic/pull/2517) [#2536](https://github.com/sanic-org/sanic/pull/2536) Add some type hints


## Version 22.6.2

### Bugfixes

- [#2522](https://github.com/sanic-org/sanic/pull/2522) Always show server location in ASGI

## Version 22.6.1

### Bugfixes

- [#2477](https://github.com/sanic-org/sanic/pull/2477) Sanic static directory fails when folder name ends with ".."


## Version 22.6.0

### Features
- [#2378](https://github.com/sanic-org/sanic/pull/2378) Introduce HTTP/3 and autogeneration of TLS certificates in `DEBUG` mode
    - 👶 *EARLY RELEASE FEATURE*: Serving Sanic over HTTP/3 is an early release feature. It does not yet fully cover the HTTP/3 spec, but instead aims for feature parity with Sanic's existing HTTP/1.1 server. Websockets, WebTransport, push responses are examples of some features not yet implemented.
    - 📦 *EXTRA REQUIREMENT*: Not all HTTP clients are capable of interfacing with HTTP/3 servers. You may need to install a [HTTP/3 capable client](https://curl.se/docs/http3.html).
    - 📦 *EXTRA REQUIREMENT*: In order to use TLS autogeneration, you must install either [mkcert](https://github.com/FiloSottile/mkcert) or [trustme](https://github.com/python-trio/trustme).
- [#2416](https://github.com/sanic-org/sanic/pull/2416) Add message to `task.cancel`
- [#2420](https://github.com/sanic-org/sanic/pull/2420) Add exception aliases for more consistent naming with standard HTTP response types (`BadRequest`, `MethodNotAllowed`, `RangeNotSatisfiable`)
- [#2432](https://github.com/sanic-org/sanic/pull/2432) Expose ASGI `scope` as a property on the `Request` object
- [#2438](https://github.com/sanic-org/sanic/pull/2438) Easier access to websocket class for annotation: `from sanic import Websocket`
- [#2439](https://github.com/sanic-org/sanic/pull/2439) New API for reading form values with options: `Request.get_form` 
- [#2445](https://github.com/sanic-org/sanic/pull/2445) Add custom `loads` function
- [#2447](https://github.com/sanic-org/sanic/pull/2447), [#2486](https://github.com/sanic-org/sanic/pull/2486) Improved API to support setting cache control headers
- [#2453](https://github.com/sanic-org/sanic/pull/2453) Move verbosity filtering to logger
- [#2475](https://github.com/sanic-org/sanic/pull/2475) Expose getter for current request using `Request.get_current()`

### Bugfixes
- [#2448](https://github.com/sanic-org/sanic/pull/2448) Fix to allow running with `pythonw.exe` or places where there is no `sys.stdout`
- [#2451](https://github.com/sanic-org/sanic/pull/2451) Trigger `http.lifecycle.request` signal in ASGI mode
- [#2455](https://github.com/sanic-org/sanic/pull/2455) Resolve typing of stacked route definitions
- [#2463](https://github.com/sanic-org/sanic/pull/2463) Properly catch websocket CancelledError in websocket handler in Python 3.7

### Deprecations and Removals
- [#2487](https://github.com/sanic-org/sanic/pull/2487) v22.6 deprecations and changes
    1. Optional application registry
    1. Execution of custom handlers after some part of response was sent
    1. Configuring fallback handlers on the `ErrorHandler`
    1. Custom `LOGO` setting
    1. `sanic.response.stream`
    1. `AsyncioServer.init`

### Developer infrastructure
- [#2449](https://github.com/sanic-org/sanic/pull/2449) Clean up `black` and `isort` config
- [#2479](https://github.com/sanic-org/sanic/pull/2479) Fix some flappy tests

### Improved Documentation
- [#2461](https://github.com/sanic-org/sanic/pull/2461) Update example to match current application naming standards
- [#2466](https://github.com/sanic-org/sanic/pull/2466) Better type annotation for `Extend`
- [#2485](https://github.com/sanic-org/sanic/pull/2485) Improved help messages in CLI


## Version 22.3.0

### Features
- [#2347](https://github.com/sanic-org/sanic/pull/2347) API for multi-application server
    - 🚨 *BREAKING CHANGE*: The old `sanic.worker.GunicornWorker` has been **removed**. To run Sanic with `gunicorn`, you should use it thru `uvicorn` [as described in their docs](https://www.uvicorn.org/#running-with-gunicorn).
    - 🧁 *SIDE EFFECT*: Named background tasks are now supported, even in Python 3.7
- [#2357](https://github.com/sanic-org/sanic/pull/2357) Parse `Authorization` header as `Request.credentials`
- [#2361](https://github.com/sanic-org/sanic/pull/2361) Add config option to skip `Touchup` step in application startup
- [#2372](https://github.com/sanic-org/sanic/pull/2372) Updates to CLI help messaging
- [#2382](https://github.com/sanic-org/sanic/pull/2382) Downgrade warnings to backwater debug messages 
- [#2396](https://github.com/sanic-org/sanic/pull/2396) Allow for `multidict` v0.6
- [#2401](https://github.com/sanic-org/sanic/pull/2401) Upgrade CLI catching for alternative application run types
- [#2402](https://github.com/sanic-org/sanic/pull/2402) Conditionally inject CLI arguments into factory
- [#2413](https://github.com/sanic-org/sanic/pull/2413) Add new start and stop event listeners to reloader process
- [#2414](https://github.com/sanic-org/sanic/pull/2414) Remove loop as required listener arg
- [#2415](https://github.com/sanic-org/sanic/pull/2415) Better exception for bad URL parsing
- [sanic-routing#47](https://github.com/sanic-org/sanic-routing/pull/47) Add a new extention parameter type: `<file:ext>`, `<file:ext=jpg>`, `<file:ext=jpg|png|gif|svg>`, `<file=int:ext>`, `<file=int:ext=jpg|png|gif|svg>`, `<file=float:ext=tar.gz>`
    - 👶 *BETA FEATURE*: This feature will not work with `path` type matching, and is being released as a beta feature only.
- [sanic-routing#57](https://github.com/sanic-org/sanic-routing/pull/57) Change `register_pattern` to accept a `str` or `Pattern`
- [sanic-routing#58](https://github.com/sanic-org/sanic-routing/pull/58) Default matching on non-empty strings only, and new `strorempty` pattern type
    - 🚨 *BREAKING CHANGE*: Previously a route with a dynamic string parameter (`/<foo>` or `/<foo:str>`) would match on any string, including empty strings. It will now **only** match a non-empty string. To retain the old behavior, you should use the new parameter type: `/<foo:strorempty>`.

### Bugfixes
- [#2373](https://github.com/sanic-org/sanic/pull/2373) Remove `error_logger` on websockets
- [#2381](https://github.com/sanic-org/sanic/pull/2381) Fix newly assigned `None` in task registry
- [sanic-routing#52](https://github.com/sanic-org/sanic-routing/pull/52) Add type casting to regex route matching
- [sanic-routing#60](https://github.com/sanic-org/sanic-routing/pull/60) Add requirements check on regex routes (this resolves, for example, multiple static directories with differing `host` values)

### Deprecations and Removals
- [#2362](https://github.com/sanic-org/sanic/pull/2362) 22.3 Deprecations and changes
    1. `debug=True` and `--debug` do _NOT_ automatically run `auto_reload`
    2. Default error render is with plain text (browsers still get HTML by default because `auto` looks at headers)
    3. `config` is required for `ErrorHandler.finalize`
    4. `ErrorHandler.lookup` requires two positional args
    5. Unused websocket protocol args removed
- [#2344](https://github.com/sanic-org/sanic/pull/2344) Deprecate loading of lowercase environment variables

### Developer infrastructure
- [#2363](https://github.com/sanic-org/sanic/pull/2363) Revert code coverage back to Codecov
- [#2405](https://github.com/sanic-org/sanic/pull/2405) Upgrade tests for `sanic-routing` changes
- [sanic-testing#35](https://github.com/sanic-org/sanic-testing/pull/35) Allow for httpx v0.22

### Improved Documentation
- [#2350](https://github.com/sanic-org/sanic/pull/2350) Fix link in README for ASGI
- [#2398](https://github.com/sanic-org/sanic/pull/2398) Document middleware on_request and on_response
- [#2409](https://github.com/sanic-org/sanic/pull/2409) Add missing documentation for `Request.respond`

### Miscellaneous
- [#2376](https://github.com/sanic-org/sanic/pull/2376) Fix typing for `ListenerMixin.listener`
- [#2383](https://github.com/sanic-org/sanic/pull/2383) Clear deprecation warning in `asyncio.wait`
- [#2387](https://github.com/sanic-org/sanic/pull/2387) Cleanup `__slots__` implementations
- [#2390](https://github.com/sanic-org/sanic/pull/2390) Clear deprecation warning in `asyncio.get_event_loop`


## Version 21.12.1

- [#2349](https://github.com/sanic-org/sanic/pull/2349) Only display MOTD on startup
- [#2354](https://github.com/sanic-org/sanic/pull/2354) Ignore name argument in Python 3.7
- [#2355](https://github.com/sanic-org/sanic/pull/2355) Add config.update support for all config values

## Version 21.12.0

### Features
- [#2260](https://github.com/sanic-org/sanic/pull/2260) Allow early Blueprint registrations to still apply later added objects
- [#2262](https://github.com/sanic-org/sanic/pull/2262) Noisy exceptions - force logging of all exceptions
- [#2264](https://github.com/sanic-org/sanic/pull/2264) Optional `uvloop` by configuration
- [#2270](https://github.com/sanic-org/sanic/pull/2270) Vhost support using multiple TLS certificates
- [#2277](https://github.com/sanic-org/sanic/pull/2277) Change signal routing for increased consistency
    - *BREAKING CHANGE*: If you were manually routing signals there is a breaking change. The signal router's `get` is no longer 100% determinative. There is now an additional step to loop thru the returned signals for proper matching on the requirements. If signals are being dispatched using `app.dispatch` or `bp.dispatch`, there is no change.
- [#2290](https://github.com/sanic-org/sanic/pull/2290) Add contextual exceptions
- [#2291](https://github.com/sanic-org/sanic/pull/2291) Increase join concat performance 
- [#2295](https://github.com/sanic-org/sanic/pull/2295), [#2316](https://github.com/sanic-org/sanic/pull/2316), [#2331](https://github.com/sanic-org/sanic/pull/2331) Restructure of CLI and application state with new displays and more command parity with `app.run`
- [#2302](https://github.com/sanic-org/sanic/pull/2302) Add route context at definition time
- [#2304](https://github.com/sanic-org/sanic/pull/2304) Named tasks and new API for managing background tasks
- [#2307](https://github.com/sanic-org/sanic/pull/2307) On app auto-reload, provide insight of changed files
- [#2308](https://github.com/sanic-org/sanic/pull/2308) Auto extend application with [Sanic Extensions](https://sanicframework.org/en/plugins/sanic-ext/getting-started.html) if it is installed, and provide first class support for accessing the extensions
- [#2309](https://github.com/sanic-org/sanic/pull/2309) Builtin signals changed to `Enum`
- [#2313](https://github.com/sanic-org/sanic/pull/2313) Support additional config implementation use case
- [#2321](https://github.com/sanic-org/sanic/pull/2321) Refactor environment variable hydration logic
- [#2327](https://github.com/sanic-org/sanic/pull/2327) Prevent sending multiple or mixed responses on a single request
- [#2330](https://github.com/sanic-org/sanic/pull/2330) Custom type casting on environment variables
- [#2332](https://github.com/sanic-org/sanic/pull/2332) Make all deprecation notices consistent
- [#2335](https://github.com/sanic-org/sanic/pull/2335) Allow underscore to start instance names

### Bugfixes
- [#2273](https://github.com/sanic-org/sanic/pull/2273) Replace assignation by typing for `websocket_handshake`
- [#2285](https://github.com/sanic-org/sanic/pull/2285) Fix IPv6 display in startup logs
- [#2299](https://github.com/sanic-org/sanic/pull/2299) Dispatch `http.lifecyle.response` from exception handler

### Deprecations and Removals
- [#2306](https://github.com/sanic-org/sanic/pull/2306) Removal of deprecated items
    - `Sanic` and `Blueprint` may no longer have arbitrary properties attached to them
    - `Sanic` and `Blueprint` forced to have compliant names
        - alphanumeric + `_` + `-`
        - must start with letter or `_`
    - `load_env` keyword argument of `Sanic`
    - `sanic.exceptions.abort`
    - `sanic.views.CompositionView`
    - `sanic.response.StreamingHTTPResponse`
        - *NOTE:* the `stream()` response method (where you pass a callable streaming function) has been deprecated and will be removed in v22.6. You should upgrade all streaming responses to the new style: https://sanicframework.org/en/guide/advanced/streaming.html#response-streaming
- [#2320](https://github.com/sanic-org/sanic/pull/2320) Remove app instance from Config for error handler setting

### Developer infrastructure
- [#2251](https://github.com/sanic-org/sanic/pull/2251) Change dev install command
- [#2286](https://github.com/sanic-org/sanic/pull/2286) Change codeclimate complexity threshold from 5 to 10
- [#2287](https://github.com/sanic-org/sanic/pull/2287) Update host test function names so they are not overwritten
- [#2292](https://github.com/sanic-org/sanic/pull/2292) Fail CI on error
- [#2311](https://github.com/sanic-org/sanic/pull/2311), [#2324](https://github.com/sanic-org/sanic/pull/2324) Do not run tests for draft PRs
- [#2336](https://github.com/sanic-org/sanic/pull/2336) Remove paths from coverage checks
- [#2338](https://github.com/sanic-org/sanic/pull/2338) Cleanup ports on tests

### Improved Documentation
- [#2269](https://github.com/sanic-org/sanic/pull/2269), [#2329](https://github.com/sanic-org/sanic/pull/2329), [#2333](https://github.com/sanic-org/sanic/pull/2333) Cleanup typos and fix language

### Miscellaneous
- [#2257](https://github.com/sanic-org/sanic/pull/2257), [#2294](https://github.com/sanic-org/sanic/pull/2294), [#2341](https://github.com/sanic-org/sanic/pull/2341) Add Python 3.10 support
- [#2279](https://github.com/sanic-org/sanic/pull/2279), [#2317](https://github.com/sanic-org/sanic/pull/2317), [#2322](https://github.com/sanic-org/sanic/pull/2322) Add/correct missing type annotations
- [#2305](https://github.com/sanic-org/sanic/pull/2305) Fix examples to use modern implementations


## Version 21.9.3
*Rerelease of v21.9.2 with some cleanup*

## Version 21.9.2
- [#2268](https://github.com/sanic-org/sanic/pull/2268) Make HTTP connections start in IDLE stage, avoiding delays and error messages
- [#2310](https://github.com/sanic-org/sanic/pull/2310) More consistent config setting with post-FALLBACK_ERROR_FORMAT apply

## Version 21.9.1
- [#2259](https://github.com/sanic-org/sanic/pull/2259) Allow non-conforming ErrorHandlers

## Version 21.9.0

### Features
- [#2158](https://github.com/sanic-org/sanic/pull/2158), [#2248](https://github.com/sanic-org/sanic/pull/2248) Complete overhaul of I/O to websockets
- [#2160](https://github.com/sanic-org/sanic/pull/2160) Add new 17 signals into server and request lifecycles
- [#2162](https://github.com/sanic-org/sanic/pull/2162) Smarter `auto` fallback formatting upon exception
- [#2184](https://github.com/sanic-org/sanic/pull/2184) Introduce implementation for copying a Blueprint
- [#2200](https://github.com/sanic-org/sanic/pull/2200) Accept header parsing
- [#2207](https://github.com/sanic-org/sanic/pull/2207) Log remote address if available
- [#2209](https://github.com/sanic-org/sanic/pull/2209) Add convenience methods to BP groups
- [#2216](https://github.com/sanic-org/sanic/pull/2216) Add default messages to SanicExceptions
- [#2225](https://github.com/sanic-org/sanic/pull/2225) Type annotation convenience for annotated handlers with path parameters
- [#2236](https://github.com/sanic-org/sanic/pull/2236) Allow Falsey (but not-None) responses from route handlers
- [#2238](https://github.com/sanic-org/sanic/pull/2238) Add `exception` decorator to Blueprint Groups
- [#2244](https://github.com/sanic-org/sanic/pull/2244) Explicit static directive for serving file or dir (ex: `static(..., resource_type="file")`)
- [#2245](https://github.com/sanic-org/sanic/pull/2245) Close HTTP loop when connection task cancelled

### Bugfixes
- [#2188](https://github.com/sanic-org/sanic/pull/2188) Fix the handling of the end of a chunked request
- [#2195](https://github.com/sanic-org/sanic/pull/2195) Resolve unexpected error handling on static requests
- [#2208](https://github.com/sanic-org/sanic/pull/2208) Make blueprint-based exceptions attach and trigger in a more intuitive manner
- [#2211](https://github.com/sanic-org/sanic/pull/2211) Fixed for handling exceptions of asgi app call
- [#2213](https://github.com/sanic-org/sanic/pull/2213) Fix bug where ws exceptions not being logged
- [#2231](https://github.com/sanic-org/sanic/pull/2231) Cleaner closing of tasks by using `abort()` in strategic places to avoid dangling sockets
- [#2247](https://github.com/sanic-org/sanic/pull/2247) Fix logging of auto-reload status in debug mode
- [#2246](https://github.com/sanic-org/sanic/pull/2246) Account for BP with exception handler but no routes

### Developer infrastructure  
- [#2194](https://github.com/sanic-org/sanic/pull/2194) HTTP unit tests with raw client
- [#2199](https://github.com/sanic-org/sanic/pull/2199) Switch to codeclimate
- [#2214](https://github.com/sanic-org/sanic/pull/2214) Try Reopening Windows Tests
- [#2229](https://github.com/sanic-org/sanic/pull/2229) Refactor `HttpProtocol` into a base class
- [#2230](https://github.com/sanic-org/sanic/pull/2230) Refactor `server.py` into multi-file module

### Miscellaneous
- [#2173](https://github.com/sanic-org/sanic/pull/2173) Remove Duplicated Dependencies and PEP 517 Support 
- [#2193](https://github.com/sanic-org/sanic/pull/2193), [#2196](https://github.com/sanic-org/sanic/pull/2196), [#2217](https://github.com/sanic-org/sanic/pull/2217) Type annotation changes


## Version 21.6.1

**Bugfixes**

-   [#2178](https://github.com/sanic-org/sanic/pull/2178) Update
    sanic-routing to allow for better splitting of complex URI
    templates
-   [#2183](https://github.com/sanic-org/sanic/pull/2183) Proper
    handling of chunked request bodies to resolve phantom 503 in logs
-   [#2181](https://github.com/sanic-org/sanic/pull/2181) Resolve
    regression in exception logging
-   [#2201](https://github.com/sanic-org/sanic/pull/2201) Cleanup
    request info in pipelined requests

## Version 21.6.0

**Features**

-   [#2094](https://github.com/sanic-org/sanic/pull/2094) Add
    `response.eof()` method for closing a stream in a handler

-   [#2097](https://github.com/sanic-org/sanic/pull/2097) Allow
    case-insensitive HTTP Upgrade header

-   [#2104](https://github.com/sanic-org/sanic/pull/2104) Explicit
    usage of CIMultiDict getters

-   [#2109](https://github.com/sanic-org/sanic/pull/2109) Consistent
    use of error loggers

-   [#2114](https://github.com/sanic-org/sanic/pull/2114) New
    `client_ip` access of connection info instance

-   [#2119](https://github.com/sanic-org/sanic/pull/2119) Alternatate
    classes on instantiation for `Config` and `Sanic.ctx`

-   [#2133](https://github.com/sanic-org/sanic/pull/2133) Implement
    new version of AST router

    -   Proper differentiation between `alpha` and `string` param
        types
    -   Adds a `slug` param type, example: `<foo:slug>`
    -   Deprecates `<foo:string>` in favor of `<foo:str>`
    -   Deprecates `<foo:number>` in favor of `<foo:float>`
    -   Adds a `route.uri` accessor

-   [#2136](https://github.com/sanic-org/sanic/pull/2136) CLI
    improvements with new optional params

-   [#2137](https://github.com/sanic-org/sanic/pull/2137) Add
    `version_prefix` to URL builders

-   [#2140](https://github.com/sanic-org/sanic/pull/2140) Event
    autoregistration with `EVENT_AUTOREGISTER`

-   [#2146](https://github.com/sanic-org/sanic/pull/2146),
    [#2147](https://github.com/sanic-org/sanic/pull/2147) Require
    stricter names on `Sanic()` and `Blueprint()`

-   [#2150](https://github.com/sanic-org/sanic/pull/2150) Infinitely
    reusable and nestable `Blueprint` and `BlueprintGroup`

-   [#2154](https://github.com/sanic-org/sanic/pull/2154) Upgrade
    `websockets` dependency to min version

-   [#2155](https://github.com/sanic-org/sanic/pull/2155) Allow for
    maximum header sizes to be increased: `REQUEST_MAX_HEADER_SIZE`

-   [#2157](https://github.com/sanic-org/sanic/pull/2157) Allow app
    factory pattern in CLI

-   [#2165](https://github.com/sanic-org/sanic/pull/2165) Change HTTP
    methods to enums

-   [#2167](https://github.com/sanic-org/sanic/pull/2167) Allow
    auto-reloading on additional directories

-   [#2168](https://github.com/sanic-org/sanic/pull/2168) Add simple
    HTTP server to CLI

-   [#2170](https://github.com/sanic-org/sanic/pull/2170) Additional
    methods for attaching `HTTPMethodView`

**Bugfixes**

-   [#2091](https://github.com/sanic-org/sanic/pull/2091) Fix
    `UserWarning` in ASGI mode for missing `__slots__`
-   [#2099](https://github.com/sanic-org/sanic/pull/2099) Fix static
    request handler logging exception on 404
-   [#2110](https://github.com/sanic-org/sanic/pull/2110) Fix
    request.args.pop removes parameters inconsistently
-   [#2107](https://github.com/sanic-org/sanic/pull/2107) Fix type
    hinting for load_env
-   [#2127](https://github.com/sanic-org/sanic/pull/2127) Make sure
    ASGI ws subprotocols is a list
-   [#2128](https://github.com/sanic-org/sanic/pull/2128) Fix issue
    where Blueprint exception handlers do not consistently route to
    proper handler

**Deprecations and Removals**

-   [#2156](https://github.com/sanic-org/sanic/pull/2156) Remove
    config value `REQUEST_BUFFER_QUEUE_SIZE`
-   [#2170](https://github.com/sanic-org/sanic/pull/2170)
    `CompositionView` deprecated and marked for removal in 21.12
-   [#2172](https://github.com/sanic-org/sanic/pull/2170) Deprecate
    StreamingHTTPResponse

**Developer infrastructure**

-   [#2149](https://github.com/sanic-org/sanic/pull/2149) Remove
    Travis CI in favor of GitHub Actions

**Improved Documentation**

-   [#2164](https://github.com/sanic-org/sanic/pull/2164) Fix typo in
    documentation
-   [#2100](https://github.com/sanic-org/sanic/pull/2100) Remove
    documentation for non-existent arguments

## Version 21.3.2

**Bugfixes**

-   [#2081](https://github.com/sanic-org/sanic/pull/2081) Disable
    response timeout on websocket connections
-   [#2085](https://github.com/sanic-org/sanic/pull/2085) Make sure
    that blueprints with no slash is maintained when applied

## Version 21.3.1

**Bugfixes**

-   [#2076](https://github.com/sanic-org/sanic/pull/2076) Static files
    inside subfolders are not accessible (404)

## Version 21.3.0

[Release
Notes](https://sanicframework.org/en/guide/release-notes/v21.3.html)

**Features**

-   [#1876](https://github.com/sanic-org/sanic/pull/1876) Unified
    streaming server
-   [#2005](https://github.com/sanic-org/sanic/pull/2005) New
    `Request.id` property
-   [#2008](https://github.com/sanic-org/sanic/pull/2008) Allow
    Pathlib Path objects to be passed to `app.static()` helper
-   [#2010](https://github.com/sanic-org/sanic/pull/2010),
    [#2031](https://github.com/sanic-org/sanic/pull/2031) New
    startup-optimized router
-   [#2018](https://github.com/sanic-org/sanic/pull/2018)
    [#2064](https://github.com/sanic-org/sanic/pull/2064) Listeners
    for main server process
-   [#2032](https://github.com/sanic-org/sanic/pull/2032) Add raw
    header info to request object
-   [#2042](https://github.com/sanic-org/sanic/pull/2042)
    [#2060](https://github.com/sanic-org/sanic/pull/2060)
    [#2061](https://github.com/sanic-org/sanic/pull/2061) Introduce
    Signals API
-   [#2043](https://github.com/sanic-org/sanic/pull/2043) Add
    `__str__` and `__repr__` to Sanic and Blueprint
-   [#2047](https://github.com/sanic-org/sanic/pull/2047) Enable
    versioning and strict slash on BlueprintGroup
-   [#2053](https://github.com/sanic-org/sanic/pull/2053) Make
    `get_app` name argument optional
-   [#2055](https://github.com/sanic-org/sanic/pull/2055) JSON encoder
    change via app
-   [#2063](https://github.com/sanic-org/sanic/pull/2063) App and
    connection level context objects

**Bugfixes**

-   Resolve [#1420](https://github.com/sanic-org/sanic/pull/1420)
    `url_for` where `strict_slashes` are on for a path ending in `/`
-   Resolve [#1525](https://github.com/sanic-org/sanic/pull/1525)
    Routing is incorrect with some special characters
-   Resolve [#1653](https://github.com/sanic-org/sanic/pull/1653) ASGI
    headers in body
-   Resolve [#1722](https://github.com/sanic-org/sanic/pull/1722)
    Using curl in chunk mode
-   Resolve [#1730](https://github.com/sanic-org/sanic/pull/1730)
    Extra content in ASGI streaming response
-   Resolve [#1749](https://github.com/sanic-org/sanic/pull/1749)
    Restore broken middleware edge cases
-   Resolve [#1785](https://github.com/sanic-org/sanic/pull/1785)
    [#1804](https://github.com/sanic-org/sanic/pull/1804) Synchronous
    error handlers
-   Resolve [#1790](https://github.com/sanic-org/sanic/pull/1790)
    Protocol errors did not support async error handlers #1790
-   Resolve [#1824](https://github.com/sanic-org/sanic/pull/1824)
    Timeout on specific methods
-   Resolve [#1875](https://github.com/sanic-org/sanic/pull/1875)
    Response timeout error from all routes after returning several
    timeouts from a specific route
-   Resolve [#1988](https://github.com/sanic-org/sanic/pull/1988)
    Handling of safe methods with body
-   [#2001](https://github.com/sanic-org/sanic/pull/2001) Raise
    ValueError when cookie max-age is not an integer

**Deprecations and Removals**

-   [#2007](https://github.com/sanic-org/sanic/pull/2007) \* Config
    using `from_envvar` \* Config using `from_pyfile` \* Config using
    `from_object`
-   [#2009](https://github.com/sanic-org/sanic/pull/2009) Remove Sanic
    test client to its own package
-   [#2036](https://github.com/sanic-org/sanic/pull/2036),
    [#2037](https://github.com/sanic-org/sanic/pull/2037) Drop Python
    3.6 support
-   `Request.endpoint` deprecated in favor of `Request.name`
-   handler type name prefixes removed (static, websocket, etc)

**Developer infrastructure**

-   [#1995](https://github.com/sanic-org/sanic/pull/1995) Create
    FUNDING.yml
-   [#2013](https://github.com/sanic-org/sanic/pull/2013) Add codeql
    to CI pipeline
-   [#2038](https://github.com/sanic-org/sanic/pull/2038) Codecov
    configuration updates
-   [#2049](https://github.com/sanic-org/sanic/pull/2049) Updated
    setup.py to use `find_packages`

**Improved Documentation**

-   [#1218](https://github.com/sanic-org/sanic/pull/1218)
    Documentation for sanic.log.\* is missing
-   [#1608](https://github.com/sanic-org/sanic/pull/1608) Add
    documentation on calver and LTS
-   [#1731](https://github.com/sanic-org/sanic/pull/1731) Support
    mounting application elsewhere than at root path
-   [#2006](https://github.com/sanic-org/sanic/pull/2006) Upgraded
    type annotations and improved docstrings and API documentation
-   [#2052](https://github.com/sanic-org/sanic/pull/2052) Fix some
    examples and docs

**Miscellaneous**

-   `Request.route` property
-   Better websocket subprotocols support
-   Resolve bug with middleware in Blueprint Group when passed
    callable
-   Moves common logic between Blueprint and Sanic into mixins
-   Route naming changed to be more consistent
    -   request endpoint is the route name
    -   route names are fully namespaced
-   Some new convenience decorators:
    -   `@app.main_process_start`
    -   `@app.main_process_stop`
    -   `@app.before_server_start`
    -   `@app.after_server_start`
    -   `@app.before_server_stop`
    -   `@app.after_server_stop`
    -   `@app.on_request`
    -   `@app.on_response`
-   Fixes `Allow` header that did not include `HEAD`
-   Using \"name\" keyword in `url_for` for a \"static\" route where
    name does not exist
-   Cannot have multiple `app.static()` without using the named param
-   Using \"filename\" keyword in `url_for` on a file route
-   `unquote` in route def (not automatic)
-   `routes_all` is tuples
-   Handler arguments are kwarg only
-   `request.match_info` is now a cached (and not computed) property
-   Unknown static file mimetype is sent as `application/octet-stream`
-   `_host` keyword in `url_for`
-   Add charset default to `utf-8` for text and js content types if
    not specified
-   Version for a route can be str, float, or int
-   Route has ctx property
-   App has `routes_static`, `routes_dynamic`, `routes_regex`
-   [#2044](https://github.com/sanic-org/sanic/pull/2044) Code cleanup
    and refactoring
-   [#2072](https://github.com/sanic-org/sanic/pull/2072) Remove
    `BaseSanic` metaclass
-   [#2074](https://github.com/sanic-org/sanic/pull/2074) Performance
    adjustments in `handle_request_`

## Version 20.12.3

**Bugfixes**

-   [#2021](https://github.com/sanic-org/sanic/pull/2021) Remove
    prefix from websocket handler name

## Version 20.12.2

**Dependencies**

-   [#2026](https://github.com/sanic-org/sanic/pull/2026) Fix uvloop
    to 0.14 because 0.15 drops Python 3.6 support
-   [#2029](https://github.com/sanic-org/sanic/pull/2029) Remove old
    chardet requirement, add in hard multidict requirement

## Version 19.12.5

**Dependencies**

-   [#2025](https://github.com/sanic-org/sanic/pull/2025) Fix uvloop
    to 0.14 because 0.15 drops Python 3.6 support
-   [#2027](https://github.com/sanic-org/sanic/pull/2027) Remove old
    chardet requirement, add in hard multidict requirement

## Version 20.12.0

**Features**

-   [#1993](https://github.com/sanic-org/sanic/pull/1993) Add disable
    app registry
-   [#1945](https://github.com/sanic-org/sanic/pull/1945) Static route
    more verbose if file not found
-   [#1954](https://github.com/sanic-org/sanic/pull/1954) Fix static
    routes registration on a blueprint
-   [#1961](https://github.com/sanic-org/sanic/pull/1961) Add Python
    3.9 support
-   [#1962](https://github.com/sanic-org/sanic/pull/1962) Sanic CLI
    upgrade
-   [#1967](https://github.com/sanic-org/sanic/pull/1967) Update
    aiofile version requirements
-   [#1969](https://github.com/sanic-org/sanic/pull/1969) Update
    multidict version requirements
-   [#1970](https://github.com/sanic-org/sanic/pull/1970) Add py.typed
    file
-   [#1972](https://github.com/sanic-org/sanic/pull/1972) Speed
    optimization in request handler
-   [#1979](https://github.com/sanic-org/sanic/pull/1979) Add app
    registry and Sanic class level app retrieval

**Bugfixes**

-   [#1965](https://github.com/sanic-org/sanic/pull/1965) Fix Chunked
    Transport-Encoding in ASGI streaming response

**Deprecations and Removals**

-   [#1981](https://github.com/sanic-org/sanic/pull/1981) Cleanup and
    remove deprecated code

**Developer infrastructure**

-   [#1956](https://github.com/sanic-org/sanic/pull/1956) Fix load
    module test
-   [#1973](https://github.com/sanic-org/sanic/pull/1973) Transition
    Travis from .org to .com
-   [#1986](https://github.com/sanic-org/sanic/pull/1986) Update tox
    requirements

**Improved Documentation**

-   [#1951](https://github.com/sanic-org/sanic/pull/1951)
    Documentation improvements
-   [#1983](https://github.com/sanic-org/sanic/pull/1983) Remove
    duplicate contents in testing.rst
-   [#1984](https://github.com/sanic-org/sanic/pull/1984) Fix typo in
    routing.rst

## Version 20.9.1

**Bugfixes**

-   [#1954](https://github.com/sanic-org/sanic/pull/1954) Fix static
    route registration on blueprints
-   [#1957](https://github.com/sanic-org/sanic/pull/1957) Removes
    duplicate headers in ASGI streaming body

## Version 19.12.3

**Bugfixes**

-   [#1959](https://github.com/sanic-org/sanic/pull/1959) Removes
    duplicate headers in ASGI streaming body

## Version 20.9.0

**Features**

-   [#1887](https://github.com/sanic-org/sanic/pull/1887) Pass
    subprotocols in websockets (both sanic server and ASGI)
-   [#1894](https://github.com/sanic-org/sanic/pull/1894)
    Automatically set `test_mode` flag on app instance
-   [#1903](https://github.com/sanic-org/sanic/pull/1903) Add new
    unified method for updating app values
-   [#1906](https://github.com/sanic-org/sanic/pull/1906),
    [#1909](https://github.com/sanic-org/sanic/pull/1909) Adds
    WEBSOCKET_PING_TIMEOUT and WEBSOCKET_PING_INTERVAL configuration
    values
-   [#1935](https://github.com/sanic-org/sanic/pull/1935) httpx
    version dependency updated, it is slated for removal as a
    dependency in v20.12
-   [#1937](https://github.com/sanic-org/sanic/pull/1937) Added auto,
    text, and json fallback error handlers (in v21.3, the default will
    change form html to auto)

**Bugfixes**

-   [#1897](https://github.com/sanic-org/sanic/pull/1897) Resolves
    exception from unread bytes in stream

**Deprecations and Removals**

-   [#1903](https://github.com/sanic-org/sanic/pull/1903)
    config.from_envar, config.from_pyfile, and config.from_object are
    deprecated and set to be removed in v21.3

**Developer infrastructure**

-   [#1890](https://github.com/sanic-org/sanic/pull/1890),
    [#1891](https://github.com/sanic-org/sanic/pull/1891) Update isort
    calls to be compatible with new API
-   [#1893](https://github.com/sanic-org/sanic/pull/1893) Remove
    version section from setup.cfg
-   [#1924](https://github.com/sanic-org/sanic/pull/1924) Adding
    \--strict-markers for pytest

**Improved Documentation**

-   [#1922](https://github.com/sanic-org/sanic/pull/1922) Add explicit
    ASGI compliance to the README

## Version 20.6.3

**Bugfixes**

-   [#1884](https://github.com/sanic-org/sanic/pull/1884) Revert
    change to multiprocessing mode

## Version 20.6.2

**Features**

-   [#1641](https://github.com/sanic-org/sanic/pull/1641) Socket
    binding implemented properly for IPv6 and UNIX sockets

## Version 20.6.1

**Features**

-   [#1760](https://github.com/sanic-org/sanic/pull/1760) Add version
    parameter to websocket routes
-   [#1866](https://github.com/sanic-org/sanic/pull/1866) Add `sanic`
    as an entry point command
-   [#1880](https://github.com/sanic-org/sanic/pull/1880) Add handler
    names for websockets for url_for usage

**Bugfixes**

-   [#1776](https://github.com/sanic-org/sanic/pull/1776) Bug fix for
    host parameter issue with lists
-   [#1842](https://github.com/sanic-org/sanic/pull/1842) Fix static
    \_handler pickling error
-   [#1827](https://github.com/sanic-org/sanic/pull/1827) Fix reloader
    on OSX py38 and Windows
-   [#1848](https://github.com/sanic-org/sanic/pull/1848) Reverse
    named_response_middlware execution order, to match normal response
    middleware execution order
-   [#1853](https://github.com/sanic-org/sanic/pull/1853) Fix pickle
    error when attempting to pickle an application which contains
    websocket routes

**Deprecations and Removals**

-   [#1739](https://github.com/sanic-org/sanic/pull/1739) Deprecate
    body_bytes to merge into body

**Developer infrastructure**

-   [#1852](https://github.com/sanic-org/sanic/pull/1852) Fix naming
    of CI test env on Python nightlies
-   [#1857](https://github.com/sanic-org/sanic/pull/1857) Adjust
    websockets version to setup.py
-   [#1869](https://github.com/sanic-org/sanic/pull/1869) Wrap
    run()\'s \"protocol\" type annotation in Optional\[\]

**Improved Documentation**

-   [#1846](https://github.com/sanic-org/sanic/pull/1846) Update docs
    to clarify response middleware execution order
-   [#1865](https://github.com/sanic-org/sanic/pull/1865) Fixing rst
    format issue that was hiding documentation

## Version 20.6.0

*Released, but unintentionally omitting PR #1880, so was replaced by
20.6.1*

## Version 20.3.0

**Features**

-   [#1762](https://github.com/sanic-org/sanic/pull/1762) Add
    `srv.start_serving()` and `srv.serve_forever()` to `AsyncioServer`
-   [#1767](https://github.com/sanic-org/sanic/pull/1767) Make Sanic
    usable on `hypercorn -k trio myweb.app`
-   [#1768](https://github.com/sanic-org/sanic/pull/1768) No
    tracebacks on normal errors and prettier error pages
-   [#1769](https://github.com/sanic-org/sanic/pull/1769) Code cleanup
    in file responses
-   [#1793](https://github.com/sanic-org/sanic/pull/1793) and
    [#1819](https://github.com/sanic-org/sanic/pull/1819) Upgrade
    `str.format()` to f-strings
-   [#1798](https://github.com/sanic-org/sanic/pull/1798) Allow
    multiple workers on MacOS with Python 3.8
-   [#1820](https://github.com/sanic-org/sanic/pull/1820) Do not set
    content-type and content-length headers in exceptions

**Bugfixes**

-   [#1748](https://github.com/sanic-org/sanic/pull/1748) Remove loop
    argument in `asyncio.Event` in Python 3.8
-   [#1764](https://github.com/sanic-org/sanic/pull/1764) Allow route
    decorators to stack up again
-   [#1789](https://github.com/sanic-org/sanic/pull/1789) Fix tests
    using hosts yielding incorrect `url_for`
-   [#1808](https://github.com/sanic-org/sanic/pull/1808) Fix Ctrl+C
    and tests on Windows

**Deprecations and Removals**

-   [#1800](https://github.com/sanic-org/sanic/pull/1800) Begin
    deprecation in way of first-class streaming, removal of
    `body_init`, `body_push`, and `body_finish`
-   [#1801](https://github.com/sanic-org/sanic/pull/1801) Complete
    deprecation from
    [#1666](https://github.com/sanic-org/sanic/pull/1666) of
    dictionary context on `request` objects.
-   [#1807](https://github.com/sanic-org/sanic/pull/1807) Remove
    server config args that can be read directly from app
-   [#1818](https://github.com/sanic-org/sanic/pull/1818) Complete
    deprecation of `app.remove_route` and `request.raw_args`

**Dependencies**

-   [#1794](https://github.com/sanic-org/sanic/pull/1794) Bump `httpx`
    to 0.11.1
-   [#1806](https://github.com/sanic-org/sanic/pull/1806) Import
    `ASGIDispatch` from top-level `httpx` (from third-party
    deprecation)

**Developer infrastructure**

-   [#1833](https://github.com/sanic-org/sanic/pull/1833) Resolve
    broken documentation builds

**Improved Documentation**

-   [#1755](https://github.com/sanic-org/sanic/pull/1755) Usage of
    `response.empty()`
-   [#1778](https://github.com/sanic-org/sanic/pull/1778) Update
    README
-   [#1783](https://github.com/sanic-org/sanic/pull/1783) Fix typo
-   [#1784](https://github.com/sanic-org/sanic/pull/1784) Corrected
    changelog for docs move of MD to RST
    ([#1691](https://github.com/sanic-org/sanic/pull/1691))
-   [#1803](https://github.com/sanic-org/sanic/pull/1803) Update
    config docs to match DEFAULT_CONFIG
-   [#1814](https://github.com/sanic-org/sanic/pull/1814) Update
    getting_started.rst
-   [#1821](https://github.com/sanic-org/sanic/pull/1821) Update to
    deployment
-   [#1822](https://github.com/sanic-org/sanic/pull/1822) Update docs
    with changes done in 20.3
-   [#1834](https://github.com/sanic-org/sanic/pull/1834) Order of
    listeners

## Version 19.12.0

**Bugfixes**

-   Fix blueprint middleware application

    Currently, any blueprint middleware registered, irrespective of
    which blueprint was used to do so, was being applied to all of the
    routes created by the `@app` and `@blueprint` alike.

    As part of this change, the blueprint based middleware application
    is enforced based on where they are registered.

    -   If you register a middleware via `@blueprint.middleware` then it
        will apply only to the routes defined by the blueprint.
    -   If you register a middleware via `@blueprint_group.middleware`
        then it will apply to all blueprint based routes that are part
        of the group.
    -   If you define a middleware via `@app.middleware` then it will be
        applied on all available routes
        ([#37](https://github.com/sanic-org/sanic/issues/37))

-   Fix [url_for]{.title-ref} behavior with missing SERVER_NAME

    If the [SERVER_NAME]{.title-ref} was missing in the
    [app.config]{.title-ref} entity, the [url_for]{.title-ref} on the
    [request]{.title-ref} and [app]{.title-ref} were failing due to an
    [AttributeError]{.title-ref}. This fix makes the availability of
    [SERVER_NAME]{.title-ref} on our [app.config]{.title-ref} an
    optional behavior.
    ([#1707](https://github.com/sanic-org/sanic/issues/1707))

**Improved Documentation**

-   Move docs from MD to RST

    Moved all docs from markdown to restructured text like the rest of
    the docs to unify the scheme and make it easier in the future to
    update documentation.
    ([#1691](https://github.com/sanic-org/sanic/issues/1691))

-   Fix documentation for [get]{.title-ref} and [getlist]{.title-ref} of
    the [request.args]{.title-ref}

    Add additional example for showing the usage of
    [getlist]{.title-ref} and fix the documentation string for
    [request.args]{.title-ref} behavior
    ([#1704](https://github.com/sanic-org/sanic/issues/1704))

## Version 19.6.3

**Features**

-   Enable Towncrier Support

    As part of this feature, [towncrier]{.title-ref} is being introduced
    as a mechanism to partially automate the process of generating and
    managing change logs as part of each of pull requests.
    ([#1631](https://github.com/sanic-org/sanic/issues/1631))

**Improved Documentation**

-   Documentation infrastructure changes
    -   Enable having a single common [CHANGELOG]{.title-ref} file for
        both GitHub page and documentation
    -   Fix Sphinix deprecation warnings
    -   Fix documentation warnings due to invalid [rst]{.title-ref}
        indentation
    -   Enable common contribution guidelines file across GitHub and
        documentation via [CONTRIBUTING.rst]{.title-ref}
        ([#1631](https://github.com/sanic-org/sanic/issues/1631))

## Version 19.6.2

**Features**

-   [#1562](https://github.com/sanic-org/sanic/pull/1562) Remove
    `aiohttp` dependency and create new `SanicTestClient` based upon
    [requests-async](https://github.com/encode/requests-async)
-   [#1475](https://github.com/sanic-org/sanic/pull/1475) Added ASGI
    support (Beta)
-   [#1436](https://github.com/sanic-org/sanic/pull/1436) Add
    Configure support from object string

**Bugfixes**

-   [#1587](https://github.com/sanic-org/sanic/pull/1587) Add missing
    handle for Expect header.
-   [#1560](https://github.com/sanic-org/sanic/pull/1560) Allow to
    disable Transfer-Encoding: chunked.
-   [#1558](https://github.com/sanic-org/sanic/pull/1558) Fix graceful
    shutdown.
-   [#1594](https://github.com/sanic-org/sanic/pull/1594) Strict
    Slashes behavior fix

**Deprecations and Removals**

-   [#1544](https://github.com/sanic-org/sanic/pull/1544) Drop
    dependency on distutil
-   [#1562](https://github.com/sanic-org/sanic/pull/1562) Drop support
    for Python 3.5
-   [#1568](https://github.com/sanic-org/sanic/pull/1568) Deprecate
    route removal.

.. warning:: Warning

    Sanic will not support Python 3.5 from version 19.6 and forward. 
    However, version 18.12LTS will have its support period extended thru
    December 2020, and therefore passing Python\'s official support version
    3.5, which is set to expire in September 2020.

## Version 19.3

**Features**

-   [#1497](https://github.com/sanic-org/sanic/pull/1497) Add support
    for zero-length and RFC 5987 encoded filename for
    multipart/form-data requests.

-   [#1484](https://github.com/sanic-org/sanic/pull/1484) The type of
    `expires` attribute of `sanic.cookies.Cookie` is now enforced to
    be of type `datetime`.

-   [#1482](https://github.com/sanic-org/sanic/pull/1482) Add support
    for the `stream` parameter of `sanic.Sanic.add_route()` available
    to `sanic.Blueprint.add_route()`.

-   [#1481](https://github.com/sanic-org/sanic/pull/1481) Accept
    negative values for route parameters with type `int` or `number`.

-   [#1476](https://github.com/sanic-org/sanic/pull/1476) Deprecated
    the use of `sanic.request.Request.raw_args` - it has a fundamental
    flaw in which is drops repeated query string parameters. Added
    `sanic.request.Request.query_args` as a replacement for the
    original use-case.

-   [#1472](https://github.com/sanic-org/sanic/pull/1472) Remove an
    unwanted `None` check in Request class `repr` implementation. This
    changes the default `repr` of a Request from `<Request>` to
    `<Request: None />`

-   [#1470](https://github.com/sanic-org/sanic/pull/1470) Added 2 new
    parameters to `sanic.app.Sanic.create_server`:

    -   `return_asyncio_server` - whether to return an
        asyncio.Server.
    -   `asyncio_server_kwargs` - kwargs to pass to
        `loop.create_server` for the event loop that sanic is using.
    >
    This is a breaking change.

-   [#1499](https://github.com/sanic-org/sanic/pull/1499) Added a set
    of test cases that test and benchmark route resolution.

-   [#1457](https://github.com/sanic-org/sanic/pull/1457) The type of
    the `"max-age"` value in a `sanic.cookies.Cookie` is now enforced
    to be an integer. Non-integer values are replaced with `0`.

-   [#1445](https://github.com/sanic-org/sanic/pull/1445) Added the
    `endpoint` attribute to an incoming `request`, containing the name
    of the handler function.

-   [#1423](https://github.com/sanic-org/sanic/pull/1423) Improved
    request streaming. `request.stream` is now a bounded-size buffer
    instead of an unbounded queue. Callers must now call
    `await request.stream.read()` instead of
    `await request.stream.get()` to read each portion of the body.

    This is a breaking change.

**Bugfixes**

-   [#1502](https://github.com/sanic-org/sanic/pull/1502) Sanic was
    prefetching `time.time()` and updating it once per second to avoid
    excessive `time.time()` calls. The implementation was observed to
    cause memory leaks in some cases. The benefit of the prefetch
    appeared to negligible, so this has been removed. Fixes
    [#1500](https://github.com/sanic-org/sanic/pull/1500)
-   [#1501](https://github.com/sanic-org/sanic/pull/1501) Fix a bug in
    the auto-reloader when the process was launched as a module i.e.
    `python -m init0.mod1` where the sanic server is started in
    `init0/mod1.py` with `debug` enabled and imports another module in
    `init0`.
-   [#1376](https://github.com/sanic-org/sanic/pull/1376) Allow sanic
    test client to bind to a random port by specifying `port=None`
    when constructing a `SanicTestClient`
-   [#1399](https://github.com/sanic-org/sanic/pull/1399) Added the
    ability to specify middleware on a blueprint group, so that all
    routes produced from the blueprints in the group have the
    middleware applied.
-   [#1442](https://github.com/sanic-org/sanic/pull/1442) Allow the
    the use the `SANIC_ACCESS_LOG` environment variable to
    enable/disable the access log when not explicitly passed to
    `app.run()`. This allows the access log to be disabled for example
    when running via gunicorn.

**Developer infrastructure**

-   [#1529](https://github.com/sanic-org/sanic/pull/1529) Update
    project PyPI credentials
-   [#1515](https://github.com/sanic-org/sanic/pull/1515) fix linter
    issue causing travis build failures (fix #1514)
-   [#1490](https://github.com/sanic-org/sanic/pull/1490) Fix python
    version in doc build
-   [#1478](https://github.com/sanic-org/sanic/pull/1478) Upgrade
    setuptools version and use native docutils in doc build
-   [#1464](https://github.com/sanic-org/sanic/pull/1464) Upgrade
    pytest, and fix caplog unit tests

**Improved Documentation**

-   [#1516](https://github.com/sanic-org/sanic/pull/1516) Fix typo at
    the exception documentation
-   [#1510](https://github.com/sanic-org/sanic/pull/1510) fix typo in
    Asyncio example
-   [#1486](https://github.com/sanic-org/sanic/pull/1486)
    Documentation typo
-   [#1477](https://github.com/sanic-org/sanic/pull/1477) Fix grammar
    in README.md
-   [#1489](https://github.com/sanic-org/sanic/pull/1489) Added
    \"databases\" to the extensions list
-   [#1483](https://github.com/sanic-org/sanic/pull/1483) Add
    sanic-zipkin to extensions list
-   [#1487](https://github.com/sanic-org/sanic/pull/1487) Removed link
    to deleted repo, Sanic-OAuth, from the extensions list
-   [#1460](https://github.com/sanic-org/sanic/pull/1460) 18.12
    changelog
-   [#1449](https://github.com/sanic-org/sanic/pull/1449) Add example
    of amending request object
-   [#1446](https://github.com/sanic-org/sanic/pull/1446) Update
    README
-   [#1444](https://github.com/sanic-org/sanic/pull/1444) Update
    README
-   [#1443](https://github.com/sanic-org/sanic/pull/1443) Update
    README, including new logo
-   [#1440](https://github.com/sanic-org/sanic/pull/1440) fix minor
    type and pip install instruction mismatch
-   [#1424](https://github.com/sanic-org/sanic/pull/1424)
    Documentation Enhancements

Note: 19.3.0 was skipped for packagement purposes and not released on
PyPI

## Version 18.12

### 18.12.0

-   Changes:

    -   Improved codebase test coverage from 81% to 91%.
    -   Added stream_large_files and host examples in static_file
        document
    -   Added methods to append and finish body content on Request
        (#1379)
    -   Integrated with .appveyor.yml for windows ci support
    -   Added documentation for AF_INET6 and AF_UNIX socket usage
    -   Adopt black/isort for codestyle
    -   Cancel task when connection_lost
    -   Simplify request ip and port retrieval logic
    -   Handle config error in load config file.
    -   Integrate with codecov for CI
    -   Add missed documentation for config section.
    -   Deprecate Handler.log
    -   Pinned httptools requirement to version 0.0.10+

-   Fixes:

    -   Fix `remove_entity_headers` helper function (#1415)
    -   Fix TypeError when use Blueprint.group() to group blueprint
        with default url_prefix, Use os.path.normpath to avoid invalid
        url_prefix like api//v1 f8a6af1 Rename the `http` module to
        `helpers` to prevent conflicts with the built-in Python http
        library (fixes #1323)
    -   Fix unittests on windows
    -   Fix Namespacing of sanic logger
    -   Fix missing quotes in decorator example
    -   Fix redirect with quoted param
    -   Fix doc for latest blueprint code
    -   Fix build of latex documentation relating to markdown lists
    -   Fix loop exception handling in app.py
    -   Fix content length mismatch in windows and other platform
    -   Fix Range header handling for static files (#1402)
    -   Fix the logger and make it work (#1397)
    -   Fix type pikcle-\>pickle in multiprocessing test
    -   Fix pickling blueprints Change the string passed in the
        \"name\" section of the namedtuples in Blueprint to match the
        name of the Blueprint module attribute name. This allows
        blueprints to be pickled and unpickled, without errors, which
        is a requirement of running Sanic in multiprocessing mode in
        Windows. Added a test for pickling and unpickling blueprints
        Added a test for pickling and unpickling sanic itself Added a
        test for enabling multiprocessing on an app with a blueprint
        (only useful to catch this bug if the tests are run on
        Windows).
    -   Fix document for logging

## Version 0.8

**0.8.3**

-   Changes:
    -   Ownership changed to org \'sanic-org\'

**0.8.0**

-   Changes:
    -   Add Server-Sent Events extension (Innokenty Lebedev)
    -   Graceful handling of request_handler_task cancellation (Ashley
        Sommer)
    -   Sanitize URL before redirection (aveao)
    -   Add url_bytes to request (johndoe46)
    -   py37 support for travisci (yunstanford)
    -   Auto reloader support for OSX (garyo)
    -   Add UUID route support (Volodymyr Maksymiv)
    -   Add pausable response streams (Ashley Sommer)
    -   Add weakref to request slots (vopankov)
    -   remove ubuntu 12.04 from test fixture due to deprecation
        (yunstanford)
    -   Allow streaming handlers in add_route (kinware)
    -   use travis_retry for tox (Raphael Deem)
    -   update aiohttp version for test client (yunstanford)
    -   add redirect import for clarity (yingshaoxo)
    -   Update HTTP Entity headers (Arnulfo Solís)
    -   Add register_listener method (Stephan Fitzpatrick)
    -   Remove uvloop/ujson dependencies for Windows (abuckenheimer)
    -   Content-length header on 204/304 responses (Arnulfo Solís)
    -   Extend WebSocketProtocol arguments and add docs (Bob Olde
        Hampsink, yunstanford)
    -   Update development status from pre-alpha to beta (Maksim
        Anisenkov)
    -   KeepAlive Timeout log level changed to debug (Arnulfo Solís)
    -   Pin pytest to 3.3.2 because of pytest-dev/pytest#3170 (Maksim
        Aniskenov)
    -   Install Python 3.5 and 3.6 on docker container for tests (Shahin
        Azad)
    -   Add support for blueprint groups and nesting (Elias Tarhini)
    -   Remove uvloop for windows setup (Aleksandr Kurlov)
    -   Auto Reload (Yaser Amari)
    -   Documentation updates/fixups (multiple contributors)
-   Fixes:
    -   Fix: auto_reload in Linux (Ashley Sommer)
    -   Fix: broken tests for aiohttp \>= 3.3.0 (Ashley Sommer)
    -   Fix: disable auto_reload by default on windows (abuckenheimer)
    -   Fix (1143): Turn off access log with gunicorn (hqy)
    -   Fix (1268): Support status code for file response (Cosmo Borsky)
    -   Fix (1266): Add content_type flag to Sanic.static (Cosmo Borsky)
    -   Fix: subprotocols parameter missing from add_websocket_route
        (ciscorn)
    -   Fix (1242): Responses for CI header (yunstanford)
    -   Fix (1237): add version constraint for websockets (yunstanford)
    -   Fix (1231): memory leak - always release resource (Phillip Xu)
    -   Fix (1221): make request truthy if transport exists (Raphael
        Deem)
    -   Fix failing tests for aiohttp\>=3.1.0 (Ashley Sommer)
    -   Fix try_everything examples (PyManiacGR, kot83)
    -   Fix (1158): default to auto_reload in debug mode (Raphael Deem)
    -   Fix (1136): ErrorHandler.response handler call too restrictive
        (Julien Castiaux)
    -   Fix: raw requires bytes-like object (cloudship)
    -   Fix (1120): passing a list in to a route decorator\'s host arg
        (Timothy Ebiuwhe)
    -   Fix: Bug in multipart/form-data parser (DirkGuijt)
    -   Fix: Exception for missing parameter when value is null
        (NyanKiyoshi)
    -   Fix: Parameter check (Howie Hu)
    -   Fix (1089): Routing issue with named parameters and different
        methods (yunstanford)
    -   Fix (1085): Signal handling in multi-worker mode (yunstanford)
    -   Fix: single quote in readme.rst (Cosven)
    -   Fix: method typos (Dmitry Dygalo)
    -   Fix: log_response correct output for ip and port (Wibowo
        Arindrarto)
    -   Fix (1042): Exception Handling (Raphael Deem)
    -   Fix: Chinese URIs (Howie Hu)
    -   Fix (1079): timeout bug when self.transport is None (Raphael
        Deem)
    -   Fix (1074): fix strict_slashes when route has slash (Raphael
        Deem)
    -   Fix (1050): add samesite cookie to cookie keys (Raphael Deem)
    -   Fix (1065): allow add_task after server starts (Raphael Deem)
    -   Fix (1061): double quotes in unauthorized exception (Raphael
        Deem)
    -   Fix (1062): inject the app in add_task method (Raphael Deem)
    -   Fix: update environment.yml for readthedocs (Eli Uriegas)
    -   Fix: Cancel request task when response timeout is triggered
        (Jeong YunWon)
    -   Fix (1052): Method not allowed response for RFC7231 compliance
        (Raphael Deem)
    -   Fix: IPv6 Address and Socket Data Format (Dan Palmer)

Note: Changelog was unmaintained between 0.1 and 0.7

## Version 0.1

**0.1.7**

-   Reversed static url and directory arguments to meet spec

**0.1.6**

-   Static files
-   Lazy Cookie Loading

**0.1.5**

-   Cookies
-   Blueprint listeners and ordering
-   Faster Router
-   Fix: Incomplete file reads on medium+ sized post requests
-   Breaking: after_start and before_stop now pass sanic as their
    first argument

**0.1.4**

-   Multiprocessing

**0.1.3**

-   Blueprint support
-   Faster Response processing

**0.1.1 - 0.1.2**

-   Struggling to update pypi via CI

**0.1.0**

-   Released to public
