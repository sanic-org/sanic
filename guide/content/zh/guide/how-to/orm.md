# ORM

> 如何使用 SQLAlchemy 和 Sanic ？

所有ORM工具都可以使用 Sanic 但非异步的 ORM 工具对Sanic 性能产生影响。
有一些或者软件包支持

目前有许多ORM支持Python的“async`/`await\`”关键字。 一些可能的选项包括：

- [Mayim](https://ahopkins.github.io/mayim/)
- [SQLAlchemy 1.4](https://docs.sqlalchemy.org/en/14/changelog/changelog_14.html)
- [tortoise-orm](https://github.com/tortoise/tortoise-orm)

您的 Sanic 应用程序的集成相当简单：

## 马伊姆

Mayim船上有[Sanic Extensions的扩展](https://ahopkins.github.io/mayim/guide/extensions.html#sanic)，这使得开始萨尼克变得非常简单。 当然可以在没有扩展的情况下运行Mayim，但是建议它处理所有的[生命周期事件](https://sanic)。 ev/en/guide/basics/listeners.html)和[依赖注入](https://sanic.dev/en/plugins/sanic-ext/injection.html)。

.. 列:

```
### Dependencies

First, we need to install the required dependencies. See [Mayim docs](https://ahopkins.github.io/mayim/guide/install.html#postgres) for the installation needed for your DB driver.
```

.. 列:

````
```shell
pip install sanic-ext
pip install mayim[postgres]
```
````

.. 列:

```
### Define ORM Model

Mayim allows you to use whatever you want for models. Whether it is [dataclasses](https://docs.python.org/3/library/dataclasses.html), [pydantic](https://pydantic-docs.helpmanual.io/), [attrs](https://www.attrs.org/en/stable/), or even just plain `dict` objects. Since it works very nicely [out of the box with Pydantic](https://ahopkins.github.io/mayim/guide/pydantic.html), that is what we will use here.
```

.. 列:

````
```python
# ./models。 y
from pydanticimporting BaseModel

class City(BaseModel):
    id: int
    name: str
    region: str
    population: int

class Country(BaseModel):
    code: str
    name: str
    continent: str
    region: str
    capital: City
```
````

.. 列:

```
### 定义SQL

如果您不熟悉，也许与其他ORM不同，因为它是单向的，SQL-先的。 这意味着您可以在内部或者在一个单独的`.sql`文件中定义自己的查询，这就是我们将在这里做的。
```

.. 列:

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

.. 列:

```
### Create Sanic App and Async Engine

We need to create the app instance and attach the `SanicMayimExtension` with any executors.
```

.. 列:

````
```python
# ./server.py
from sanic import Sanic, Request, json
from sanic_ext import Exten
from mayim.expertor import Postgresultor
from mayim. xtenes import SanicMayimextension
from model import Country

class CountryExecutor(Postgresultor):
    async def select_all_countries(
        self, 限制：int = 4 偏移：int = 0
    ) -> 列表[Country]:
        .

app = Sanic("测试")
Extend。 egister(
    SanicMayimExtension(
        expertors=[CountryExecutor],
        dsn="postgres://。 .",
    (
)
```
````

.. 列:

```
### 注册航线

因为我们正在使用 Mayim's 扩展 Sanic, 我们在路由处理器中自动注入了 "CountryExecutor" 。 它使人们能够轻松地获得附加类型说明的发展经验。
```

.. 列:

````
```python
@app.get("/")
async def handler(request: Request, executor: CountryExecutor):
    countries = required executor.select_all_countries()
    return json({"countries": [country.dict() for country in co
```
````

.. 列:

```
### 发送请求
```

.. 列:

````
```sh
curl 'http://127.0.0.1:8000'
{"countries":[{"code":"AFG","name":"Afghanistan","continent":"Asia","region":"Southern and Central Asia","capital":{"id":1,"name":"Kabul","district":"Kabol","population":1780000}},{"code":"ALB","name":"Albania","continent":"Europe","region":"Southern Europe","capital":{"id":34,"name":"Tirana","district":"Tirana","population":270000}},{"code":"DZA","name":"Algeria","continent":"Africa","region":"Northern Africa","capital":{"id":35,"name":"Alger","district":"Alger","population":2168000}},{"code":"ASM","name":"American Samoa","continent":"Oceania","region":"Polynesia","capital":{"id":54,"name":"Fagatogo","district":"Tutuila","population":2323}}]}
```
````

## SQLAlchemy

因为[SQLAlchemy 1.4](https://docs.sqlalchemy.org/en/14/changelog/changelog_14.html)添加了本机支持`asyncio`, Sanic最终可以与 SQLAlchemy 进行很好的工作。 请注意，SQLAlchemy项目仍然认为此功能是_测试版_。

.. 列:

```
### Dependencies

First, we need to install the required dependencies. In the past, the dependencies installed were `sqlalchemy` and `pymysql`, but now `sqlalchemy` and `aiomysql` are needed.
```

.. 列:

````
```shell
pip install -U sqlalchemy
pip install -U aiomysql
```
````

.. 列:

```
### 定义ORM Model

ORM model 创建保持不变。
```

.. 列:

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

.. 列:

```
### Create Sanic App and Async Engine

Here we use mysql as the database, and you can also choose PostgreSQL/SQLite. Pay attention to changing the driver from `aiomysql` to `asyncpg`/`aiosqlite`.
```

.. 列:

````
```python
# ./server.py
from sanic import Sanic
from sqlalchemy.ext.asyncio import create_async_engine

app = Sanic("my_app")

bind = create_async_engine("mysql+aiomysql://root:root@localhost/test", echo=True)
```
````

.. 列:

```
### Register Middlewares

The request middleware creates an usable `AsyncSession` object and set it to `request.ctx` and `_base_model_session_ctx`.

Thread-safe variable `_base_model_session_ctx` helps you to use the session object instead of fetching it from `request.ctx`.
```

.. 列:

````
```python
# ./server.py
from contextVar Import ContextVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy rm importing sessionmaker

_sessionmaker = sessionmaker(bind, AsyncSession, expire_on_commit=False)

_base_model_session_ctx = ContextVar("session")

@app.middleware("request")
async def inject_session(request):
    request. tx.session = _sessionmaker()
    request.ctx.session_ctx_token = _base_model_session_ctx.set(request.ctx.session)

@app.middleware("response")
async def close_session(request, response):
    if havasttrac(request). tx, "session_ctx_token"):
        _base_model_session_ctx.reset(crequest.ctx.session_ctx_token)
        等待request.ctx.session.close()
```
````

.. 列:

```
### Register Routes

According to sqlalchemy official docs, `session.query` will be legacy in 2.0, and the 2.0 way to query an ORM object is using `select`.
```

.. 列:

````
```python
# ./server.py
from sqlalchemy import selected
from sqlalchemy.orm import selectinload
from sanic. esponse importer json

from models importing Car, Person

@app.post("/user")
async def create_user(request):
    session = request。 tx.session
    异步与会话。 egin():
        car = Car(brand="Tesla")
        person = Person(name="foo", cars=[car]()
        会话。 dd_all([person])
    return json(person). o_dict())

@app.get("/user/<pk:int>")
async def get_user(request, pk):
    session = request。 tx.session
    async with session.begin():
        stmt = select(Person).where(Person.id == pk). ptions(selectinload(Person.cars))
        results = 等待会话。 xecute(stmt)
        persons = result。 calar()

    如果不是个人，则为：
        return json({})

    return json(person). o_dict())
```
````

.. 列:

```
### 发送请求
```

.. 列:

````
```sh
curl --location --request POST 'http://127.0.0.1:8000/user'
{"name":"foo","cars":[[{"brand":"Tesla"}]}
``

```sh
curl --location --request GET 'http://127.0.0.1:8000/user/1'
{"name":"foo","cars":[{"brand":"Tesla"}]}
```
````

## Tortoise-ORM

.. 列:

```
### 依赖项

tortoise-orm 的依赖关系非常简单，您只需要安装 tortoise-orm 。
```

.. 列:

````
```shell
pip安装-U tortoise-orm
```
````

.. 列:

```
### 定义ORM Model

如果你熟悉Django，你应该发现这一部分非常熟悉。
```

.. 列:

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

.. 列:

```
### 创建 Sanic App 和 Async 引擎

Tortoise-orm 提供了一套注册界面。 这对用户是方便的，您可以使用它来轻松地创建数据库连接。
```

.. 列:

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

.. 列:

```
### 注册路由
```

.. 列:

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

.. 列:

```
### 发送请求
```

.. 列:

````
```sh
curl --location --request POST 'http://127.0.0.1:8000/user'
{"users":["I are foo", "I are bar"]}
```\

```sh
curl --location --request GET 'http://127。 0.0.1:8000/user/1'
{"user": "我是foot"}
```
````

