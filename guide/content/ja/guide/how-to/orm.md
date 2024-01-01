# ORM

> どのように私はSanicでSQLAlchemyを使用しますか?

すべてのORMツールはSanicで使用できますが、非同期ORMツールはSanicパフォーマンスに影響を与えます。
サポートする Orm パッケージがいくつかあります

現在、Python の `async`/`await` キーワードをサポートするORMがたくさんあります。 いくつかの可能な選択肢には：

- [Mayim](https://ahopkins.github.io/mayim/)
- [SQLAlchemy 1.4](https://docs.sqlalchemy.org/ja/14/changelog/changelog_14.html)
- [tortoise-orm](https://github.com/tortoise/turtoise-orm)

Sanicアプリケーションへの統合はかなり簡単です:

## Mayim

Mayimはformat@@0(https\://ahopkins.github.io/mayim/guide/extensions.html#sanic)と一緒に出荷します。 確かに拡張機能なしで Mayim を実行することは可能ですが、すべての format@@0(https\://sanic )を処理するために推奨されています。 ev/ja/guide/basics/listeners.html) and [dependency injections](https://sanic.dev/en/plugins/sanic-ext/injection.html)

.. 列::

```
### 依存関係

まず、必要な依存関係をインストールする必要があります。DBドライバに必要なインストールについては、[Mayim docs](https://ahopkins.github.io/mayim/guide/install.html#postgres)を参照してください。
```

.. 列::

````
```shell
pip install sanic-ext
pip install mayim[postgres]
```
````

.. 列::

```
### Define ORM Model

Mayim allows you to use whatever you want for models. Whether it is [dataclasses](https://docs.python.org/3/library/dataclasses.html), [pydantic](https://pydantic-docs.helpmanual.io/), [attrs](https://www.attrs.org/en/stable/), or even just plain `dict` objects. Since it works very nicely [out of the box with Pydantic](https://ahopkins.github.io/mayim/guide/pydantic.html), that is what we will use here.
```

.. 列::

````
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
````

.. 列::

```
### SQLを定義する

使い慣れていない場合、Mayimは一方向のSQL-firstであるという点で他のORMとは異なります。 これは、インラインまたは別の `.sql` ファイルで独自のクエリを定義することを意味します。
```

.. 列::

````
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
````

.. 列::

```
### Sanic App と Async Engine

アプリインスタンスを作成し、任意の実行者に `SanicMayimExtension` を追加する必要があります。
```

.. 列::

````
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
````

.. 列::

```
### ルート登録

Sanic用のMayimの拡張機能を使っているので、ルートハンドラに自動的に`CountryExecutor`を注入しています。 これにより、タイプ注釈付きの開発が容易になります。
```

.. 列::

````
```python
@app.get("/")
async def handler(request, executor: CountryExecutor):
    countles = await executor.select_all_countries()
    return json({"countries": [country.dict() for country in co
```
````

.. 列::

```
### リクエストを送信する
```

.. 列::

````
```sh
curl 'http://127.0.0.1:8000'
{"countries":[{"code":"AFG","name":"Afghanistan","continent":"Asia","region":"Southern and Central Asia","capital":{"id":1,"name":"Kabul","district":"Kabol","population":1780000}},{"code":"ALB","name":"Albania","continent":"Europe","region":"Southern Europe","capital":{"id":34,"name":"Tirana","district":"Tirana","population":270000}},{"code":"DZA","name":"Algeria","continent":"Africa","region":"Northern Africa","capital":{"id":35,"name":"Alger","district":"Alger","population":2168000}},{"code":"ASM","name":"American Samoa","continent":"Oceania","region":"Polynesia","capital":{"id":54,"name":"Fagatogo","district":"Tutuila","population":2323}}]}
```
````

## SQLAlchemy

[SQLAlchemy 1.4](https://docs.sqlalchemy.org/en/14/changelog/changelog_14.html) が `asyncio` のネイティブサポートを追加したため、Sanic は SQLAlchemy でうまく動作します。 この機能はまだ SQLAlchemy プロジェクトで _beta_ とみなされていることに注意してください。

.. 列::

```
### 依存関係

まず、必要な依存関係をインストールする必要があります。 以前はインストールされていた依存関係は `sqlalcemy` と `pymysql` でしたが、現在は `sqlalcemy` と `aiomysql` が必要です。
```

.. 列::

````
```shell
pip install -U sqlalchemy
pip install -U aiomysql
```
````

.. 列::

```
### Define ORM Model

ORM model creation remains the same.
```

.. 列::

````
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
````

.. 列::

```
### Sanic AppとAsync Engine

ここではデータベースとしてmysqlを使用し、PostgreSQL/SQLiteを選択することもできます。 ドライバを`aiomysql`から`asyncpg`/`aiosqlite`に変更することに注意してください。
```

.. 列::

````
```python
# ./server.py
from sanic import Sanic
from sqlalchemy.ext.asyncio import create_async_engine

app = Sanic("my_app")

bind = create_async_engine("mysql+aiomysql://root:root@localhost/test", echo=True)
```
````

.. 列::

```
### Register Middlewares

The request middleware creates an usable `AsyncSession` object and set it to `request.ctx` and `_base_model_session_ctx`.

Thread-safe variable `_base_model_session_ctx` helps you to use the session object instead of fetching it from `request.ctx`.
```

.. 列::

````
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
````

.. 列::

```
### Register Routes

によると、 sqlalcemy の公式ドキュメント、 `session. uery`は2.0でレガシーとなり、ORMオブジェクトに問い合わせる2.0の方法は`select`を使用しています。
```

.. 列::

````
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
````

.. 列::

```
### リクエストを送信する
```

.. 列::

````
```sh
curl --location --request POST 'http://127.0.0.1:8000/user'
{"name":"foo","cars":[{"brand":"Tesla"}]}
```sh

```sh
curl --location ---request GET 'http://127.0.0.1:8000/user/1'
{"name":"foo","cars":[{"brand":"Tesla"}]}
```
````

## Tortoise-ORM

.. 列::

```
### 依存関係

tortoise-ormの依存関係はとてもシンプルで、インストールするだけで済みます。
```

.. 列::

````
```shell
pip install -U tortoise-orm
```
````

.. 列::

```
### Define ORM Model

Djangoに慣れていれば、この部分はよく知っているはずです。
```

.. 列::

````
```python
# ./models.py
from tortoise import Model, fields

class Users(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(50)

    def __str__(self):
        return f"I am {self.name}"
```
````

.. 列::

```
### Create Sanic App and Async Engine

Tortoise-ormは登録インターフェースのセットを提供しています。 利用者にとって便利で、簡単にデータベース接続を作成することができます。
```

.. 列::

````
```python
# ./main.py

from models import Users
from tortoise.contrib.sanic import register_tortoise

app = Sanic(__name__)

register_tortoise(
    app, db_url="mysql://root:root@localhost/test", modules={"models": ["models"]}, generate_schemas=True
)

```
````

.. 列::

```
### ルート登録
```

.. 列::

````
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
````

.. 列::

```
### リクエストを送信する
```

.. 列::

````
```sh
curl --location --request POST 'http://127.0.0.1:8000/user'
{"users":["I am foo", "I am bar"]}
```

```sh
curl --location --request GET 'http://127.0.0.1:8000/user/1'
{"user": "I am foo"}
```
````
