---
title: Sanic Extensions - Dependency Injection
---

# Dependency Injection

Dependency injection is a method to add arguments to a route handler based upon the defined function signature. Specifically, it looks at the **type annotations** of the arguments in the handler. This can be useful in a number of cases like:

- Fetching an object based upon request headers (like the current session user)
- Recasting certain objects into a specific type
- Using the request object to prefetch data
- Auto inject services

The `Extend` instance has two basic methods on it used for dependency injection: a lower level `add_dependency`, and a higher level `dependency`. 

**Lower level**: `app.ext.add_dependency(...)`

- `type: Type,`: some unique class that will be the type of the object
- `constructor: Optional[Callable[..., Any]],` (OPTIONAL): a function that will return that type

**Higher level**: `app.ext.dependency(...)`

- `obj: Any`: any object that you would like injected
- `name: Optional[str]`: some name that could alternately be used as a reference

Let's explore some use cases here.


.. warning:: 

    If you used dependency injection prior to v21.12, the lower level API method was called `injection`. It has since been renamed to `add_dependency` and starting in v21.12 `injection` is an alias for `add_dependency`. The `injection` method has been deprecated for removal in v22.6.



## Basic implementation

The simplest use case would be simply to recast a value.

.. column::

    This could be useful if you have a model that you want to generate based upon the matched path parameters.

.. column::

    ```python
    @dataclass
    class IceCream:
        flavor: str

        def __str__(self) -> str:
            return f"{self.flavor.title()} (Yum!)"

    app.ext.add_dependency(IceCream)

    @app.get("/<flavor:str>")
    async def ice_cream(request, flavor: IceCream):
        return text(f"You chose: {flavor}")
    ```

    ```
    $ curl localhost:8000/chocolate
    You chose Chocolate (Yum!)
    ```


.. column::

    This works by passing a keyword argument to the constructor of the `type` argument. The previous example is equivalent to this.

.. column::

    ```python
    flavor = IceCream(flavor="chocolate")
    ```

## Additional constructors

.. column::

    Sometimes you may need to also pass a constructor. This could be a function, or perhaps even a classmethod that acts as a constructor. In this example, we are creating an injection that will call `Person.create` first.

    Also important to note on this example, we are actually injecting **two (2)** objects! It of course does not need to be this way, but we will inject objects based upon the function signature.

.. column::

    ```python
    @dataclass
    class PersonID:
        person_id: int

    @dataclass
    class Person:
        person_id: PersonID
        name: str
        age: int

        @classmethod
        async def create(cls, request: Request, person_id: int):
            return cls(person_id=PersonID(person_id), name="noname", age=111)


    app.ext.add_dependency(Person, Person.create)
    app.ext.add_dependency(PersonID)

    @app.get("/person/<person_id:int>")
    async def person_details(
        request: Request, person_id: PersonID, person: Person
    ):
        return text(f"{person_id}\n{person}")
    ```

    ```
    $ curl localhost:8000/person/123
    PersonID(person_id=123)
    Person(person_id=PersonID(person_id=123), name='noname', age=111)
    ```

When a `constructor` is passed to `ext.add_dependency` (like in this example) that will be called. If not, then the object will be created by calling the `type`. A couple of important things to note about passing a `constructor`:

1. A positional `request: Request` argument is *usually* expected. See the `Person.create` method above as an example using a `request` and [arbitrary constructors](#arbitrary-constructors) for how to use a callable that does not require a `request`.
1. All matched path parameters are injected as keyword arguments.
1. Dependencies can be chained and nested. Notice how in the previous example the `Person` dataclass has a `PersonID`? That means that `PersonID` will be called first, and that value is added to the keyword arguments when calling `Person.create`.

## Arbitrary constructors

.. column::

    Sometimes you may want to construct your injectable _without_ the `Request` object. This is useful if you have arbitrary classes or functions that create your objects. If the callable does have any required arguments, then they should themselves be injectable objects.

    This is very useful if you have services or other types of objects that should only exist for the lifetime of a single request. For example, you might use this pattern to pull a single connection from your database pool.

.. column::

    ```python
    class Alpha:
        ...

    class Beta:
        def __init__(self, alpha: Alpha) -> None:
            self.alpha = alpha

    app.ext.add_dependency(Alpha)
    app.ext.add_dependency(Beta)

    @app.get("/beta")
    async def handler(request: Request, beta: Beta):
        assert isinstance(beta.alpha, Alpha)
    ```

*Added in v22.9*

## Objects from the `Request`

.. column::

    Sometimes you may want to extract details from the request and preprocess them. You could, for example, cast the request JSON to a Python object, and then add some additional logic based upon DB queries.

    .. warning:: 

        If you plan to use this method, you should note that the injection actually happens *before* Sanic has had a chance to read the request body. The headers should already have been consumed. So, if you do want access to the body, you will need to manually consume as seen in this example.

        ```python
            await request.receive_body()
        ```


        This could be used in cases where you otherwise might:

        - use middleware to preprocess and add something to the `request.ctx`
        - use decorators to preprocess and inject arguments into the request handler

        In this example, we are using the `Request` object in the `compile_profile` constructor to run a fake DB query to generate and return a `UserProfile` object.

.. column::

    ```python
    @dataclass
    class User:
        name: str

    @dataclass
    class UserProfile:
        user: User
        age: int = field(default=0)
        email: str = field(default="")

        def __json__(self):
            return ujson.dumps(
                {
                    "name": self.user.name,
                    "age": self.age,
                    "email": self.email,
                }
            )

    async def fake_request_to_db(body):
        today = date.today()
        email = f'{body["name"]}@something.com'.lower()
        difference = today - date.fromisoformat(body["birthday"])
        age = int(difference.days / 365)
        return UserProfile(
            User(body["name"]),
            age=age,
            email=email,
        )

    async def compile_profile(request: Request):
        await request.receive_body()
        profile = await fake_request_to_db(request.json)
        return profile

    app.ext.add_dependency(UserProfile, compile_profile)

    @app.patch("/profile")
    async def update_profile(request, profile: UserProfile):
        return json(profile)
    ```

    ```
    $ curl localhost:8000/profile -X PATCH -d '{"name": "Alice", "birthday": "2000-01-01"}'
    {
        "name":"Alice",
        "age":21,
        "email":"alice@something.com"
    }
    ```

## Injecting services

It is a common pattern to create things like database connection pools and store them on the `app.ctx` object. This makes them available throughout your application, which is certainly a convenience. One downside, however, is that you no longer have a typed object to work with. You can use dependency injections to fix this. First we will show the concept using the lower level `add_dependency` like we have been using in the previous examples. But, there is a better way using the higher level `dependency` method.

### The lower level API using `add_dependency`

.. column::


    This works very similar to the [last example](#objects-from-the-request) where the goal is the extract something from the `Request` object. In this example, a database object was created on the `app.ctx` instance, and is being returned in the dependency injection constructor.

.. column::

    ```python
    class FakeConnection:
        async def execute(self, query: str, **arguments):
            return "result"

    @app.before_server_start
    async def setup_db(app, _):
        app.ctx.db_conn = FakeConnection()
        app.ext.add_dependency(FakeConnection, get_db)

    def get_db(request: Request):
        return request.app.ctx.db_conn



    @app.get("/")
    async def handler(request, conn: FakeConnection):
        response = await conn.execute("...")
        return text(response)
    ```
    ```
    $ curl localhost:8000/
    result
    ```

### The higher level API using `dependency`

.. column::

    Since we have an actual *object* that is available when adding the dependency injection, we can use the higher level `dependency` method. This will make the pattern much easier to write.

    This method should always be used when you want to inject something that exists throughout the lifetime of the application instance and is not request specific. It is very useful for services, third party clients, and connection pools since they are not request specific.

.. column::

    ```python
    class FakeConnection:
        async def execute(self, query: str, **arguments):
            return "result"

    @app.before_server_start
    async def setup_db(app, _):
        db_conn = FakeConnection()
        app.ext.dependency(db_conn)

    @app.get("/")
    async def handler(request, conn: FakeConnection):
        response = await conn.execute("...")
        return text(response)
    ```
    ```
    $ curl localhost:8000/
    result
    ```

## Generic types

Be carefule when using a [generic type](https://docs.python.org/3/library/typing.html#typing.Generic). The way that Sanic's dependency injection works is by matching the entire type definition. Therefore, `Foo` is not the same as `Foo[str]`. This can be particularly tricky when trying to use the [higher-level `dependency` method](#the-higher-level-api-using-dependency) since the type is inferred.

.. column::

    For example, this will **NOT** work as expected since there is no definition for `Test[str]`.

.. column::

    ```python
    import typing
    from sanic import Sanic, text

    T = typing.TypeVar("T")

    class Test(typing.Generic[T]):
        test: T

    app = Sanic("testapp")
    app.ext.dependency(Test())

    @app.get("/")
    def test(request, test: Test[str]):
        ...
    ```


.. column::

    To get this example to work, you will need to add an explicit definition for the type you intend to be injected.

.. column::

    ```python
    import typing
    from sanic import Sanic, text

    T = typing.TypeVar("T")

    class Test(typing.Generic[T]):
        test: T

    app = Sanic("testapp")
    _singleton = Test()
    app.ext.add_dependency(Test[str], lambda: _singleton)

    @app.get("/")
    def test(request, test: Test[str]):
        ...
    ```

## Configuration

.. column::

    By default, dependencies will be injected after the `http.routing.after` [signal](../../guide/advanced/signals.md#built-in-signals). Starting in v22.9, you can change this to the `http.handler.before` signal.

.. column::

    ```python
    app.config.INJECTION_SIGNAL = "http.handler.before"
    ```

*Added in v22.9*
