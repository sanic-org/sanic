# 检查员

Sanic 检查员是Sanic Server的一个特征。 在使用内置的 [工人经理] (./manager.md) 运行 Sanic 时，它是唯一可用的。

这是一个 HTTP 应用程序_可选_在您的应用程序后台运行，允许您与运行中的应用程序的实例进行交互。

.. tip:: INFO

```
在v22.9中，检查员的能力有限，但本页上的文件假定您正在使用v22.12或更多。
```

## 正在开始

检查员默认是禁用的。 要启用它，您有两个选项。

.. 列:

```
在创建应用程序实例时设置一个标记。
```

.. 列:

````
```python
app = Sanic("TestApp", inspector=True)
```
````

.. 列:

```
或者设置一个配置值。
```

.. 列:

````
```python
app = Sanic("测试应用")
app.config.INSPECTOR = True
```
````

.. 警告：:

```
如果您正在使用配置值，它*必须在主工作流程开始之前尽早完成。 这意味着它要么应该是一个环境变量，要么应该在创建上文所示的应用程序实例之后马上设定。
```

## 使用检查器

一旦检查员运行，您将可以通过 CLI 或通过 HTTP 直接访问 Web API 访问它。

.. 列:

````
**Via CLI**
```sh
sanic inspection
```
````

.. 列:

````
**通过 HTTP**
```sh
curl http://localhost:6457
```
````

.. 注：

```
请记住，检查员没有在您的 Sanic 应用程序上运行。它是一个分隔过程，具有一个分隔的应用程序，并且在一个隔绝的套接字上暴露。
```

## 内置命令

检查员带着以下内置命令。

| CLI 命令   | HTTP 操作                            | 描述                  |
| -------- | ---------------------------------- | ------------------- |
| `检查`     | `GET /`                            | 显示正在运行的应用程序的基本细节。   |
| `检查重新加载` | `POST /重新加载`                       | 触发所有服务器员工的重新加载。     |
| \`检查关机'  | `POST /shutdown`                   | 触发所有进程的关闭。          |
| `检查比例N`  | `POST /scale`<br>`{"replicas": N}` | 缩放工人数量。 `N`是复制的目标数。 |

## 自定义命令

检查员很容易添加自定义命令(和终点)。

.. 列:

```
将`Inspector`类子类并创建任意方法。 只要方法名称前面没有下划线(`_`)， 然后方法的名称将是视察员上的一个新的子命令。
```

.. 列:

````
```python
从Sanic.worker导入json
n旁观导入检查员

class MyInspector(Inspector):
    async def something(self, *args, **kwargs：
        print(args)
        print(kwargs)

app = Sanic("测试应用", spector_class=MyInspector, spector=True)
```
````

这将会显示常规模式中的自定义方法：

- CLI: `sanic inspection <method_name>`
- HTTP: `POST /<method_name>`

必须指出，新方法接受的参数来自你打算如何使用命令。 例如，上面的“something”方法接受所有基于位置和关键字的参数。

.. 列:

```
在 CLI 中，位置和关键字参数作为您方法的定位或关键词参数传递。 所有值都将是一个 `str` 但有以下例外情况:

- 一个没有分配值的关键字参数将是: `True`
- 除非参数前缀为 `no `, 然后它将是：`False`
```

.. 列:

````
```sh
sanic 检查了两个--four --no-five --six=6
``
在您的应用程序日志控制台中， 你会看到：
```
('one', 'tw', 'three')
{'four': True, 'five': False, 'six': '6'}
```
````

.. 列:

```
直接点击 API 可以实现同样的目标。您可以在 JSON 有效载荷中将参数传递到方法中。 唯一需要注意的是，位置参数应该以`{"args": [...] }`的形式暴露。
```

.. 列:

````
```sh
curl http://localhost:6457/something \
  --json '{"args":["one", "two", "three"], "four":true, "five":false, "six":6}'
```
In your application log console, you will see:
```
('one', 'two', 'three')
{'four': True, 'five': False, 'six': 6}
```
````

## 在生产中使用

.. 危险：:

```
在向检查员展示产品之前，请仔细考虑本节中的所有选项。
```

当在远程生产实例中运行检查员时，您可以通过需要 TLS 加密和需要 API 密钥认证来保护端点。

### TLS 加密

.. 列:

```
通过 TLS 向检查员HTTP 实例将路径传递到您的证书和密钥。
```

.. 列:

````
```python
app.config.INSPECTOR_TLS_CERT = "/path/to/cert.pem"
app.config.INSPECTOR_TLS_KEY = "/path/to/key.pem"
```
````

.. 列:

```
这将需要使用 "--secure" 标志或 "https://"。
```

.. 列:

`````
```sh
sanic inspection --secure --host=<somewhere>
````
```sh
curl https:////<somewhere>:6457
```
`````

### API 密钥认证

.. 列:

```
您可以通过持单人令牌身份验证来保护 API。
```

.. 列:

````
```python
app.config.INSPECTOR_API_KEY = "Super-Secret-200"
```
````

.. 列:

```
这将需要 "--api-key" 参数，或无记者令牌授权标题。
```

.. 列:

````
```sh
sanic inspect --api-key=Super-Secret-200
```
```sh
curl http://localhost:6457  -H "Authorization: Bearer Super-Secret-200"
```
````

## 配置

See [configuration](./configuration.md)
