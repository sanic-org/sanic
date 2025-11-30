---
title: 无声扩展 - 便捷性
---

# 便捷性

## 固定序列转换器

.. 列:

```
在开发应用程序时，往往会有某些路径总是返回同样的响应。 如果情况如此，您可以预定义返回序列转换器和端点。 然后所有需要返回的都是内容。
```

.. 列:

````
```python
from sanic_ext import serializer

@app.get("/<name>")
@serializer(text)
async def hello_world(request, name: str):
    if name.isnumeric():
        return "hello " * int(name)
    return f"Hello, {name}"
```
````

.. 列:

```
`序列化器`装饰器也可以添加状态码。
```

.. 列:

````
```python
from sanic_ext import serializer

@app.post("/")
@serializer(text, status=202)
async def create_something(request):
    ...
```
````

## 自定义序列转换器

.. 列:

```
使用 `@serializer` 装饰器，您也可以传递您自己的自定义函数只要他们返回一个有效的类型(`HTTPResonse`)。
```

.. 列:

````
```python
def message(retval, request, action, status):
    return json(
        {
            "request_id": str(request.id),
            "action": action,
            "message": retval,
        },
        status=status,
    )

@app.post("/<action>")
@serializer(message)
async def do_action(request, action: str):
    return "This is a message"
```
````

.. 列:

```
现在，返回一个字符串应该返回一个很好的序列化输出。
```

.. 列:

````
```python
$ curl localhost:8000/eat_cookies -X POST
own
  "request_id": "ef81c45b-235c-46ddd-b50f8fa77f9",
  "action": "eat_cookies",
  "message": "这是一个消息"
}

```
````

## 请求计数器

.. 列:

```
Sanic 扩展有一个子类的 `Request` ，可以设置来自动跟踪每个工人进程处理的请求数量。 为了启用此功能，您应该将 ' CountedRequest` 类传递给您的应用程序contrator。
```

.. 列:

````
```python
来自sanic_ext import CountedRequest

app = Sanic(...request_class=CountedRequest)
```
````

.. 列:

```
您现在将能够访问在工人整个过程中服务的请求数量。
```

.. 列:

````
```python
@app.get("/")
async def handler(request: CountedRequest):
    return json({"count": request.count})
```
````

如果可能，请求计数也将被添加到[工人状态](../../guide/running/manager.md#worker-state)。

![](https://user-images.githubusercontent.com/166269/190922460-43bd2cfc-f81a-443b-b84f-07b6ce475cbf.png)
