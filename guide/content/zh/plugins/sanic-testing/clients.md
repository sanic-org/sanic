---
title: Sanic 测试-测试客户端
---

# 测试客户端

您有三个不同的测试客户端，每个客户端具有不同的能力。

## 常规同步客户端： `SanicTestClient`

`SanicTestClient` 在您的本地网络上运行一个实际版本的 Sanic Server 来运行测试程序。 每次调用端点时，它会旋转应用程序的版本，并将它绑定到主机OS上的套接字。 然后，它将使用 `httpx` 直接拨打该应用程序。

这是测试Sanic应用的典型方式。

.. 列:

```
安装 Sanic 测试后，普通的 `SanicTestClient` 可以在不需要进一步设置的情况下使用。 这是因为Sanic在树枝下为你工作。 
```

.. 列:

````
```python
app.test_client.get("/path/to/endpoint")

````

.. 列:

```
然而，您可能会发现自己需要实例化客户端。
```

.. 列:

````
```python
from sanic_testing.testimate importing SanicTestClient

test_client = SanicTestClient(app)
test_client.get("/path/to/endpoint")
```
````

.. 列:

```
开始测试客户端的第三个选项是使用 `TestManager` 。 这个方便对象同时设置 `SanicTestClient` 和 `SanicASGITestClient` 。
```

.. 列:

````
```python
来自sanic_testination TestManager

mgr = TestManager(app)
app.test_client.get("/path/to/endpoint")
# 或
mgr.test_client.get("/path/to/endpoint")
```
````

您可以通过以下方法之一提出请求

- `SanicTestClient.get`
- `SanicTestClient.post`
- `SanicTestClient.put`
- `SanicTestClient.patch`
- `SanicTestClient.delete`
- `SanicTestClient.options`
- `SanicTestClient.head`
- `SanicTestClient.websocket`
- `SanicTestClient.request`

您可以使用这些方法 _almost_ 和您使用 `httpx`时的相同方法。 你传递到`httpx`的任何参数都将被接受，**有一个警告**：如果你在使用`test_client。 赤道`并想手动指定 HTTP 方法，你应该使用: `http_method`:

```python
test_client.request("/path/to/endpoint", http_method="get")
```

## ASGI async client: `SanicASGITestClient`

不同于“SanicTestClient”在每个请求上旋转服务器，`SanicASGITestClient`不是。 相反，它使用`httpx`库来执行 Sanic 作为ASGI 应用程序来到内部并执行路由处理器。

.. 列:

```
此测试客户端提供了所有相同的方法，通常与“SanicTestClient”相同。 唯一的区别是您需要在每次通话中添加一个 "等待" ：
```

.. 列:

````
```python
等待app.test_client.get("/path/to/endpoint")

````

`SanicASGITestClient`可以用与`SanicTestClient`完全相同的三种方式使用。

.. 注：

```
`SanicASGITestClient` 不需要只能用于ASGI 应用程序。 类似于“SanicTestClient”不需要只测试同步端点。这两个客户端都能测试*任何*无声应用程序。
```

## 持久服务客户端: `ReusableClient`

此客户端在类似于`SanicTestClient`的前提下工作，因为它代表了您应用程序的实例，并且向它提出了真正的 HTTP 请求。 然而，与`SanicTestClient`不同的是，当使用 `ReusableClient` 时，你会控制应用程序的生命周期。

这意味着每个请求 **不** 启动一个新的 web 服务器。 相反，您将根据需要启动并停止服务器，并且可以向同一个运行中的实例多次提出请求。

.. 列:

```
不同于其他两个客户端，您**必须** 实例化此客户端：
```

.. 列:

````
```python
来自sanic_testing.reusableClient

client = ReusableClient(app)
```
````

.. 列:

```
一旦创建，您将在上下文管理器中使用客户端。一旦管理器超出范围，服务器将关闭。
```

.. 列:

````
```python
来自sanic_testing。 可用于导入可重复使用的客户端

def test_multiple_endpoints_on_same_server(app):
    客户端= ReusableClient(app)
    带客户端:
        _, 响应 = 客户端。 et("/path/to/1")
        要求响应。 tatus == 200

        _, 响应 = 客户。 et("/path/to/2")
        claim response.status == 200
```
````
