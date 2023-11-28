# ORM

>  How do I use SQLAlchemy with Sanic ?

All ORM tools can work with Sanic, but non-async ORM tool have a impact on Sanic performance.
There are some orm packages who support

At present, there are many ORMs that support Python's `async`/`await` keywords. Some possible choices include：

- [Mayim](https://ahopkins.github.io/mayim/)
- [SQLAlchemy 1.4](https://docs.sqlalchemy.org/en/14/changelog/changelog_14.html)
- [tortoise-orm](https://github.com/tortoise/tortoise-orm)

Integration in to your Sanic application is fairly simple:

## Mayim

Mayim ships with [an extension for Sanic Extensions](https://ahopkins.github.io/mayim/guide/extensions.html#sanic), which makes it super simple to get started with Sanic. It is certainly possible to run Mayim with Sanic without the extension, but it is recommended because it handles all of the [lifecycle events](https://sanic.dev/en/guide/basics/listeners.html) and [dependency injections](https://sanic.dev/en/plugins/sanic-ext/injection.html).

.. column::

    ### Dependencies

    First, we need to install the required dependencies. See [Mayim docs](https://ahopkins.github.io/mayim/guide/install.html#postgres) for the installation needed for your DB driver.

.. column::

    ```shell
    pip install sanic-ext
    pip install mayim[postgres]
    ```


.. column::

    ### Define ORM Model

    Mayim allows you to use whatever you want for models. Whether it is [dataclasses](https://docs.python.org/3/library/dataclasses.html), [pydantic](https://pydantic-docs.helpmanual.io/), [attrs](https://www.attrs.org/en/stable/), or even just plain `dict` objects. Since it works very nicely [out of the box with Pydantic](https://ahopkins.github.io/mayim/guide/pydantic.html), that is what we will use here.

.. column::

    ```python
    # ./models.py
    from pydantic import BaseModel

    class City(BaseModel):
        id: int
        name: str
        district: str
        population: int

    class Country(BaseModel):
        code: str
        name: str
        continent: str
        region: str
        capital: City
    ```


.. column::

    ### Define SQL

    If you are unfamiliar, Mayim is different from other ORMs in that it is one-way, SQL-first. This means you define your own queries either inline, or in a separate `.sql` file, which is what we will do here.

.. column::

    ```sql
    -- ./queries/select_all_countries.sql
    SELECT country.code,
        country.name,
        country.continent,
        country.region,
        (
            SELECT row_to_json(q)
            FROM (
                    SELECT city.id,
                        city.name,
                        city.district,
                        city.population
                ) q
        ) capital
    FROM country
        JOIN city ON country.capital = city.id
    ORDER BY country.name ASC
    LIMIT $limit OFFSET $offset;
    ```


.. column::

    ### Create Sanic App and Async Engine

    We need to create the app instance and attach the `SanicMayimExtension` with any executors.

.. column::

    ```python
    # ./server.py
    from sanic import Sanic, Request, json
    from sanic_ext import Extend
    from mayim.executor import PostgresExecutor
    from mayim.extensions import SanicMayimExtension
    from models import Country

    class CountryExecutor(PostgresExecutor):
        async def select_all_countries(
            self, limit: int = 4, offset: int = 0
        ) -> list[Country]:
            ...

    app = Sanic("Test")
    Extend.register(
        SanicMayimExtension(
            executors=[CountryExecutor],
            dsn="postgres://...",
        )
    )
    ```


.. column::

    ### Register Routes

    Because we are using Mayim's extension for Sanic, we have the automatic `CountryExecutor` injection into the route handler. It makes for an easy, type-annotated development experience.

.. column::

    ```python
    @app.get("/")
    async def handler(request: Request, executor: CountryExecutor):
        countries = await executor.select_all_countries()
        return json({"countries": [country.dict() for country in co
    ```


.. column::

    ### Send Requests

.. column::

    ```sh
    curl 'http://127.0.0.1:8000'
    {"countries":[{"code":"AFG","name":"Afghanistan","continent":"Asia","region":"Southern and Central Asia","capital":{"id":1,"name":"Kabul","district":"Kabol","population":1780000}},{"code":"ALB","name":"Albania","continent":"Europe","region":"Southern Europe","capital":{"id":34,"name":"Tirana","district":"Tirana","population":270000}},{"code":"DZA","name":"Algeria","continent":"Africa","region":"Northern Africa","capital":{"id":35,"name":"Alger","district":"Alger","population":2168000}},{"code":"ASM","name":"American Samoa","continent":"Oceania","region":"Polynesia","capital":{"id":54,"name":"Fagatogo","district":"Tutuila","population":2323}}]}
    ```


## SQLAlchemy

Because [SQLAlchemy 1.4](https://docs.sqlalchemy.org/en/14/changelog/changelog_14.html) has added native support for `asyncio`, Sanic can finally work well with SQLAlchemy. Be aware that this functionality is still considered *beta* by the SQLAlchemy project.


.. column::

    ### Dependencies

    First, we need to install the required dependencies. In the past, the dependencies installed were `sqlalchemy` and `pymysql`, but now `sqlalchemy` and `aiomysql` are needed.

.. column::

    ```shell
    pip install -U sqlalchemy
    pip install -U aiomysql
    ```


.. column::

    ### Define ORM Model

    ORM model creation remains the same.

.. column::

    ```python
    # ./models.py
    from sqlalchemy import INTEGER, Column, ForeignKey, String
    from sqlalchemy.orm import declarative_base, relationship

    Base = declarative_base()

    class BaseModel(Base):
        __abstract__ = True
        id = Column(INTEGER(), primary_key=True)

    class Person(BaseModel):
        __tablename__ = "person"
        name = Column(String())
        cars = relationship("Car")

        def to_dict(self):
            return {"name": self.name, "cars": [{"brand": car.brand} for car in self.cars]}

    class Car(BaseModel):
        __tablename__ = "car"

        brand = Column(String())
        user_id = Column(ForeignKey("person.id"))
        user = relationship("Person", back_populates="cars")
    ```


.. column::

    ### Create Sanic App and Async Engine

    Here we use mysql as the database, and you can also choose PostgreSQL/SQLite. Pay attention to changing the driver from `aiomysql` to `asyncpg`/`aiosqlite`.

.. column::

    ```python
    # ./server.py
    from sanic import Sanic
    from sqlalchemy.ext.asyncio import create_async_engine

    app = Sanic("my_app")

    bind = create_async_engine("mysql+aiomysql://root:root@localhost/test", echo=True)
    ```


.. column::

    ### Register Middlewares

    The request middleware creates an usable `AsyncSession` object and set it to `request.ctx` and `_base_model_session_ctx`.

    Thread-safe variable `_base_model_session_ctx` helps you to use the session object instead of fetching it from `request.ctx`.

.. column::

    ```python
    # ./server.py
    from contextvars import ContextVar

    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

    _sessionmaker = sessionmaker(bind, AsyncSession, expire_on_commit=False)

    _base_model_session_ctx = ContextVar("session")

    @app.middleware("request")
    async def inject_session(request):
        request.ctx.session = _sessionmaker()
        request.ctx.session_ctx_token = _base_model_session_ctx.set(request.ctx.session)

    @app.middleware("response")
    async def close_session(request, response):
        if hasattr(request.ctx, "session_ctx_token"):
            _base_model_session_ctx.reset(request.ctx.session_ctx_token)
            await request.ctx.session.close()
    ```


.. column::

    ### Register Routes

    According to sqlalchemy official docs, `session.query` will be legacy in 2.0, and the 2.0 way to query an ORM object is using `select`.

.. column::

    ```python
    # ./server.py
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from sanic.response import json

    from models import Car, Person

    @app.post("/user")
    async def create_user(request):
        session = request.ctx.session
        async with session.begin():
            car = Car(brand="Tesla")
            person = Person(name="foo", cars=[car])
            session.add_all([person])
        return json(person.to_dict())

    @app.get("/user/<pk:int>")
    async def get_user(request, pk):
        session = request.ctx.session
        async with session.begin():
            stmt = select(Person).where(Person.id == pk).options(selectinload(Person.cars))
            result = await session.execute(stmt)
            person = result.scalar()

        if not person:
            return json({})

        return json(person.to_dict())
    ```


.. column::

    ### Send Requests

.. column::

    ```sh
    curl --location --request POST 'http://127.0.0.1:8000/user'
    {"name":"foo","cars":[{"brand":"Tesla"}]}
    ```

    ```sh
    curl --location --request GET 'http://127.0.0.1:8000/user/1'
    {"name":"foo","cars":[{"brand":"Tesla"}]}
    ```


## Tortoise-ORM

.. column::

    ### Dependencies

    tortoise-orm's dependency is very simple, you just need install tortoise-orm.

.. column::

    ```shell
    pip install -U tortoise-orm
    ```


.. column::

    ### Define ORM Model

    If you are familiar with Django, you should find this part very familiar.

.. column::

    ```python
    # ./models.py
    from tortoise import Model, fields

    class Users(Model):
        id = fields.IntField(pk=True)
        name = fields.CharField(50)

        def __str__(self):
            return f"I am {self.name}"
    ```



.. column::

    ### Create Sanic App and Async Engine

    Tortoise-orm provides a set of registration interface, which is convenient for users, and you can use it to create database connection easily.

.. column::

    ```python
    # ./main.py

    from models import Users
    from tortoise.contrib.sanic import register_tortoise

    app = Sanic(__name__)

    register_tortoise(
        app, db_url="mysql://root:root@localhost/test", modules={"models": ["models"]}, generate_schemas=True
    )

    ```


.. column::

    ### Register Routes

.. column::

    ```python
    # ./main.py

    from models import Users
    from sanic import Sanic, response

    @app.route("/user")
    async def list_all(request):
        users = await Users.all()
        return response.json({"users": [str(user) for user in users]})

    @app.route("/user/<pk:int>")
    async def get_user(request, pk):
        user = await Users.query(pk=pk)
        return response.json({"user": str(user)})

    if __name__ == "__main__":
        app.run(port=5000)
    ```


.. column::

    ### Send Requests

.. column::

    ```sh
    curl --location --request POST 'http://127.0.0.1:8000/user'
    {"users":["I am foo", "I am bar"]}
    ```

    ```sh
    curl --location --request GET 'http://127.0.0.1:8000/user/1'
    {"user": "I am foo"}
    ```

