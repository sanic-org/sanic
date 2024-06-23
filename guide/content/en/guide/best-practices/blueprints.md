# Blueprints

## Overview

Blueprints are objects that can be used for sub-routing within an application. Instead of adding routes to the application instance, blueprints define similar methods for adding routes, which are then registered with the application in a flexible and pluggable manner.

Blueprints are especially useful for larger applications, where your application logic can be broken down into several groups or areas of responsibility.

## Creating and registering

.. column::

    First, you must create a blueprint. It has a very similar API as the `Sanic()` app instance with many of the same decorators.

.. column::

    ```python
    # ./my_blueprint.py
    from sanic.response import json
    from sanic import Blueprint

    bp = Blueprint("my_blueprint")

    @bp.route("/")
    async def bp_root(request):
        return json({"my": "blueprint"})
    ```



.. column::

    Next, you register it with the app instance.

.. column::

    ```python
    from sanic import Sanic
    from my_blueprint import bp

    app = Sanic(__name__)
    app.blueprint(bp)
    ```

Blueprints also have the same `websocket()` decorator and `add_websocket_route` method for implementing websockets.

.. column::

    Beginning in v21.12, a Blueprint may be registered before or after adding objects to it. Previously, only objects attached to the Blueprint at the time of registration would be loaded into application instance.

.. column::

    ```python
    app.blueprint(bp)

    @bp.route("/")
    async def bp_root(request):
        ...
    ```

## Copying

.. column::

    Blueprints along with everything that is attached to them can be copied to new instances using the `copy()` method. The only required argument is to pass it a new `name`. However, you could also use this to override any of the values from the old blueprint.

.. column::

    ```python
    v1 = Blueprint("Version1", version=1)

    @v1.route("/something")
    def something(request):
        pass

    v2 = v1.copy("Version2", version=2)

    app.blueprint(v1)
    app.blueprint(v2)
    ```

    ```
    Available routes:
    /v1/something
    /v2/something

    ```

*Added in v21.9*

## Blueprint groups

Blueprints may also be registered as part of a list or tuple, where the registrar will recursively cycle through any sub-sequences of blueprints and register them accordingly. The Blueprint.group method is provided to simplify this process, allowing a ‘mock’ backend directory structure mimicking what’s seen from the front end. Consider this (quite contrived) example:

```text
api/
├──content/
│ ├──authors.py
│ ├──static.py
│ └──__init__.py
├──info.py
└──__init__.py
app.py
```

.. column::

    #### First blueprint

.. column::

    ```python
    # api/content/authors.py
    from sanic import Blueprint

    authors = Blueprint("content_authors", url_prefix="/authors")
    ```


.. column::

    #### Second blueprint

.. column::

    ```python
    # api/content/static.py
    from sanic import Blueprint

    static = Blueprint("content_static", url_prefix="/static")
    ```


.. column::

    #### Blueprint group

.. column::

    ```python
    # api/content/__init__.py
    from sanic import Blueprint
    from .static import static
    from .authors import authors

    content = Blueprint.group(static, authors, url_prefix="/content")
    ```


.. column::

    #### Third blueprint

.. column::

    ```python
    # api/info.py
    from sanic import Blueprint

    info = Blueprint("info", url_prefix="/info")
    ```


.. column::

    #### Another blueprint group

.. column::

    ```python
    # api/__init__.py
    from sanic import Blueprint
    from .content import content
    from .info import info

    api = Blueprint.group(content, info, url_prefix="/api")
    ```


.. column::

    #### Main server

    All blueprints are now registered

.. column::

    ```python
    # app.py
    from sanic import Sanic
    from .api import api

    app = Sanic(__name__)
    app.blueprint(api)
    ```

### Blueprint group prefixes and composability

As shown in the code above, when you create a group of blueprints you can extend the URL prefix of all the blueprints in the group by passing the `url_prefix` argument to the `Blueprint.group` method. This is useful for creating a mock directory structure for your API.


In addition, there is a `name_prefix` argument that can be used to make blueprints reusable and composable. The is specifically necessary when applying a single blueprint to multiple groups. By doing this, the blueprint will be registered with a unique name for each group, which allows the blueprint to be registered multiple times and have its routes each properly named with a unique identifier.

.. column::

    Consider this example. The routes built will be named as follows:
    - `TestApp.group-a_bp1.route1`
    - `TestApp.group-a_bp2.route2`
    - `TestApp.group-b_bp1.route1`
    - `TestApp.group-b_bp2.route2`

.. column::

    ```python
    bp1 = Blueprint("bp1", url_prefix="/bp1")
    bp2 = Blueprint("bp2", url_prefix="/bp2")

    bp1.add_route(lambda _: ..., "/", name="route1")
    bp2.add_route(lambda _: ..., "/", name="route2")

    group_a = Blueprint.group(
        bp1, bp2, url_prefix="/group-a", name_prefix="group-a"
    )
    group_b = Blueprint.group(
        bp1, bp2, url_prefix="/group-b", name_prefix="group-b"
    )

    app = Sanic("TestApp")
    app.blueprint(group_a)
    app.blueprint(group_b)
    ```

*Name prefixing added in v23.6*


## Middleware

.. column::

    Blueprints can also have middleware that is specifically registered for its endpoints only.

.. column::

    ```python
    @bp.middleware
    async def print_on_request(request):
        print("I am a spy")

    @bp.middleware("request")
    async def halt_request(request):
        return text("I halted the request")

    @bp.middleware("response")
    async def halt_response(request, response):
        return text("I halted the response")
    ```


.. column::

    Similarly, using blueprint groups, it is possible to apply middleware to an entire group of nested blueprints.

.. column::

    ```python
    bp1 = Blueprint("bp1", url_prefix="/bp1")
    bp2 = Blueprint("bp2", url_prefix="/bp2")

    @bp1.middleware("request")
    async def bp1_only_middleware(request):
        print("applied on Blueprint : bp1 Only")

    @bp1.route("/")
    async def bp1_route(request):
        return text("bp1")

    @bp2.route("/<param>")
    async def bp2_route(request, param):
        return text(param)

    group = Blueprint.group(bp1, bp2)

    @group.middleware("request")
    async def group_middleware(request):
        print("common middleware applied for both bp1 and bp2")

    # Register Blueprint group under the app
    app.blueprint(group)
    ```

## Exceptions

.. column::

    Just like other [exception handling](./exceptions.md), you can define blueprint specific handlers.

.. column::

    ```python
    @bp.exception(NotFound)
    def ignore_404s(request, exception):
        return text("Yep, I totally found the page: {}".format(request.url))
    ```

## Static files

.. column::

    Blueprints can also have their own static handlers

.. column::

    ```python
    bp = Blueprint("bp", url_prefix="/bp")
    bp.static("/web/path", "/folder/to/serve")
    bp.static("/web/path", "/folder/to/server", name="uploads")
    ```


.. column::

    Which can then be retrieved using `url_for()`. See [routing](/guide/basics/routing.md) for more information.

.. column::

    ```python
    >>> print(app.url_for("static", name="bp.uploads", filename="file.txt"))
    '/bp/web/path/file.txt'
    ```

## Listeners

.. column::

    Blueprints can also implement [listeners](/guide/basics/listeners.md).

.. column::

    ```python
    @bp.listener("before_server_start")
    async def before_server_start(app, loop):
        ...

    @bp.listener("after_server_stop")
    async def after_server_stop(app, loop):
        ...
    ```

## Versioning

As discussed in the [versioning section](/guide/advanced/versioning.md), blueprints can be used to implement different versions of a web API.

.. column::

    The `version` will be prepended to the routes as `/v1` or `/v2`, etc.

.. column::

    ```python
    auth1 = Blueprint("auth", url_prefix="/auth", version=1)
    auth2 = Blueprint("auth", url_prefix="/auth", version=2)
    ```


.. column::

    When we register our blueprints on the app, the routes `/v1/auth` and `/v2/auth` will now point to the individual blueprints, which allows the creation of sub-sites for each API version.

.. column::

    ```python
    from auth_blueprints import auth1, auth2

    app = Sanic(__name__)
    app.blueprint(auth1)
    app.blueprint(auth2)
    ```


.. column::

    It is also possible to group the blueprints under a `BlueprintGroup` entity and version multiple of them together at the
    same time.

.. column::

    ```python
    auth = Blueprint("auth", url_prefix="/auth")
    metrics = Blueprint("metrics", url_prefix="/metrics")

    group = Blueprint.group(auth, metrics, version="v1")

    # This will provide APIs prefixed with the following URL path
    # /v1/auth/ and /v1/metrics
    ```

## Composable

A `Blueprint` may be registered to multiple groups, and each of `BlueprintGroup` itself could be registered and nested further. This creates a limitless possibility `Blueprint` composition.

*Added in v21.6*

.. column::

    Take a look at this example and see how the two handlers are actually mounted as five (5) distinct routes.

.. column::

    ```python
    app = Sanic(__name__)
    blueprint_1 = Blueprint("blueprint_1", url_prefix="/bp1")
    blueprint_2 = Blueprint("blueprint_2", url_prefix="/bp2")
    group = Blueprint.group(
        blueprint_1,
        blueprint_2,
        version=1,
        version_prefix="/api/v",
        url_prefix="/grouped",
        strict_slashes=True,
    )
    primary = Blueprint.group(group, url_prefix="/primary")

    @blueprint_1.route("/")
    def blueprint_1_default_route(request):
        return text("BP1_OK")

    @blueprint_2.route("/")
    def blueprint_2_default_route(request):
        return text("BP2_OK")

    app.blueprint(group)
    app.blueprint(primary)
    app.blueprint(blueprint_1)

    # The mounted paths:
    # /api/v1/grouped/bp1/
    # /api/v1/grouped/bp2/
    # /api/v1/primary/grouped/bp1
    # /api/v1/primary/grouped/bp2
    # /bp1

    ```


## Generating a URL

When generating a url with `url_for()`, the endpoint name will be in the form:

```text
{blueprint_name}.{handler_name}
```
