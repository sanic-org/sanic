---
title: Sanic 扩展 - 验证
---

# 验证

网络应用程序最常用的功能之一是用户输入验证。 由于明显的原因，这不仅是一个安全问题，而且也是一个明显的良好做法。 你想要确保你的数据符合预期，并且在没有响应时扔出一个 \`400'。

## 二． 执行情况

### 与 Dataclasses 验证

随着[Data Classes](https://docs.python.org/3/library/dataclasses.html)的引入，Python使得创建符合定义模式的对象变得非常简单。 但是，标准库只支持类型检查验证， **不** 运行时间验证。 Sanic 扩展增加了使用`dataclasses`从方框中下载的请求进行运行时验证的能力。 如果你也安装了"pydantic"或"景点"，你也可以使用这些库中的一个。

.. 列:

```
首先，定义一个模型。
```

.. 列:

````
```python
@dataclass
class SearchParams:
    q: str
```
````

.. 列:

```
然后将其附加到您的路由
```

.. 列:

````
```python
from sanic_ext import validate

@app.route("/search")
@validate(query=SearchParams)
async def handler(request, query: SearchParams):
    return json(asdict(query))
```
````

.. 列:

```
您现在应该对传入请求进行验证。
```

.. 列:

````
``
$ curl localhost:8000/search                                       
⚠️ 400 - Bad Request
==============
无效的请求正文: 搜索参数 错误：缺少一个必需的参数：'q'
```
```
$ curl localhost:8000/search\? =python                             
{"q":"python"}
```
````

### 使用 Pydantic验证

您也可以使用 Pydantic模型。

.. 列:

```
首先，定义一个模型。
```

.. 列:

````
```python
class Person(BaseModel):
    name: str
    age: int
```
````

.. 列:

```
然后将其附加到您的路由
```

.. 列:

````
```python
from sanic_ext import valides

@app.post("/person")
@validate(json=Person)
async def handler(request, body: Person):
    return json(Body.dict())
```
````

.. 列:

```
您现在应该对传入请求进行验证。
```

.. 列:

````
```
$ curl localhost:8000/personn -d '{"name": "Alice", "age": 21}" -X POST  
{"name":"Alice","age":21}
```
````

### 使用Attrs进行验证

您也可以使用Attrso。

.. 列:

```
首先，定义一个模型。
```

.. 列:

````
```python
@trans.define
class person:
    name: str
    age: int

```
````

.. 列:

```
然后将其附加到您的路由
```

.. 列:

````
```python
from sanic_ext import valides

@app.post("/person")
@validate(json=Person)
async def handler(request, body: Person):
    return json(Body))
```
````

.. 列:

```
您现在应该对传入请求进行验证。
```

.. 列:

````
```
$ curl localhost:8000/personn -d '{"name": "Alice", "age": 21}" -X POST  
{"name":"Alice","age":21}
```
````

## 什么可以验证？

`validate`装饰符可以用来验证来自三个地方的用户数据：JSON body data (\`request ). 这种情况可能会影响到国家的经济和社会经济利益。

.. 列:

```
正如您可能期望的那样，您可以使用装饰器的关键字参数附上您的模型。
```

.. 列:

````
```python
@validate(
    json=ModelA,
    query=ModelB,
    form=ModelC,
)
```
````

