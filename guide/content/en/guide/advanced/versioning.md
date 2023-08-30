# Versioning

It is standard practice in API building to add versions to your endpoints. This allows you to easily differentiate incompatible endpoints when you try and change your API down the road in a breaking manner.

Adding a version will add a `/v{version}` url prefix to your endpoints.

The version can be a `int`, `float`, or `str`. Acceptable values:

- `1`, `2`, `3`
- `1.1`, `2.25`, `3.0`
- `"1"`, `"v1"`, `"v1.1"`

## Per route

.. column::

    You can pass a version number to the routes directly.

.. column::

    ```python
    # /v1/text
    @app.route("/text", version=1)
    def handle_request(request):
        return response.text("Hello world! Version 1")

    # /v2/text
    @app.route("/text", version=2)
    def handle_request(request):
        return response.text("Hello world! Version 2")
    ```

## Per Blueprint

.. column::

    You can also pass a version number to the blueprint, which will apply to all routes in that blueprint.

.. column::

    ```python
    bp = Blueprint("test", url_prefix="/foo", version=1)

    # /v1/foo/html
    @bp.route("/html")
    def handle_request(request):
        return response.html("<p>Hello world!</p>")
    ```

## Per Blueprint Group

.. column::

    In order to simplify the management of the versioned blueprints, you can provide a version number in the blueprint
    group. The same will be inherited to all the blueprint grouped under it if the blueprints don't already override the
    same information with a value specified while creating a blueprint instance.

    When using blueprint groups for managing the versions, the following order is followed to apply the Version prefix to
    the routes being registered.

    1. Route Level configuration
    2. Blueprint level configuration
    3. Blueprint Group level configuration

    If we find a more pointed versioning specification, we will pick that over the more generic versioning specification
    provided under the Blueprint or Blueprint Group

.. column::

    ```python
    from sanic.blueprints import Blueprint
    from sanic.response import json

    bp1 = Blueprint(
        name="blueprint-1",
        url_prefix="/bp1",
        version=1.25,
    )
    bp2 = Blueprint(
        name="blueprint-2",
        url_prefix="/bp2",
    )

    group = Blueprint.group(
        [bp1, bp2],
        url_prefix="/bp-group",
        version="v2",
    )

    # GET /v1.25/bp-group/bp1/endpoint-1
    @bp1.get("/endpoint-1")
    async def handle_endpoint_1_bp1(request):
        return json({"Source": "blueprint-1/endpoint-1"})

    # GET /v2/bp-group/bp2/endpoint-2
    @bp2.get("/endpoint-1")
    async def handle_endpoint_1_bp2(request):
        return json({"Source": "blueprint-2/endpoint-1"})

    # GET /v1/bp-group/bp2/endpoint-2
    @bp2.get("/endpoint-2", version=1)
    async def handle_endpoint_2_bp2(request):
        return json({"Source": "blueprint-2/endpoint-2"})
    ```

## Version prefix

As seen above, the `version` that is applied to a route is **always** the first segment in the generated URI path. Therefore, to make it possible to add path segments before the version, every place that a `version` argument is passed, you can also pass `version_prefix`. 

The `version_prefix` argument can be defined in:

- `app.route` and `bp.route` decorators (and all the convenience decorators also)
- `Blueprint` instantiation
- `Blueprint.group` constructor
- `BlueprintGroup` instantiation
- `app.blueprint` registration

If there are definitions in multiple places, a more specific definition overrides a more general. This list provides that hierarchy.

The default value of `version_prefix` is `/v`.

.. column::

    An often requested feature is to be able to mount versioned routes on `/api`. This can easily be accomplished with `version_prefix`.

.. column::

    ```python
    # /v1/my/path
    app.route("/my/path", version=1, version_prefix="/api/v")
    ```


.. column::

    Perhaps a more compelling usage is to load all `/api` routes into a single `BlueprintGroup`.

.. column::

    ```python
    # /v1/my/path
    app = Sanic(__name__)
    v2ip = Blueprint("v2ip", url_prefix="/ip", version=2)
    api = Blueprint.group(v2ip, version_prefix="/api/version")

    # /api/version2/ip
    @v2ip.get("/")
    async def handler(request):
        return text(request.ip)

    app.blueprint(api)
    ```

We can therefore learn that a route's URI is:

```
version_prefix + version + url_prefix + URI definition
```


.. tip:: 
    
    Just like with `url_prefix`, it is possible to define path parameters inside a `version_prefix`. It is perfectly legitimate to do this. Just remember that every route will have that parameter injected into the handler.

    ```python
    version_prefix="/<foo:str>/v"
    ```


*Added in v21.6*
