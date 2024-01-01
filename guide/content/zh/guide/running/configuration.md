# 配置

## 基础知识

.. 列:

```
Sanic持有应用程序对象配置属性中的配置。 配置对象只是一个可以使用点符号或像字典修改的对象。
```

.. 列:

````
```python
app = Sanic("myapp")
app.config.DB_NAME = "appdb"
app.config["DB_USER"] = "appuser"
```
````

.. 列:

```
您也可以使用 `update()` 方法，例如在常规字典上。
```

.. 列:

````
```python
db_settings= {
    'DB_HOST': 'localhost',
    'DB_NAME': 'appdb',
    'DB_USER': 'appuser'
}
app.config.update(db_settings)
```
````

.. 注：

```
萨尼克的标准练习是在 **大写字母** 中命名您的配置值。 确实，如果你开始混合大写和小写地名，你可能会遇到奇怪的行为。
```

## 正在加载

### 环境变量

.. 列:

```
任何通过 `SANIC_` 前缀定义的环境变量都将被应用到 Sanic 配置。 例如，设置 `SANIC_REQUEST_TIMEOUT` 将被自动加载，并输入`REQUEST_TIMEOUT` 配置变量。
```

.. 列:

````
```bash
$ export SANIC_REQUEST_TIMEOUT=10
```
```python
>> > print(app.config.REQUEST_TIMEOUT)
10
```
````

.. 列:

```
您可以更改Sanic 在启动时预期的前缀。
```

.. 列:

````
```bash
$ export MYAPP_REQUEST_TIMEOUT=10
```
```python
>>> app = Sanic(__name__, env_prefix='MYAPP_')
>>> print(app.config.REQUEST_TIMEOUT)
10
```
````

.. 列:

```
您也可以完全禁用环境变量。
```

.. 列:

````
```python
app = Sanic(__name__, load_env=False)
```
````

### 正在使用 Sanic.update_config

`Sanic` 实例有一个用于加载配置的所有_多功能方法：`app.update_config`。 你可以为它提供到文件的路径、字典、类或任何其他类型的对象。

#### 从文件

.. 列:

```
让我们说你有看起来像这样的 `my_config.py` 文件。
```

.. 列:

````
```python
# my_config.py
A = 1
B = 2
```
````

.. 列:

```
您可以通过将其路径传递给`app.update_config`来加载它作为配置值。
```

.. 列:

````
```python
>>> app.update_config("/path/to/my_config.py")
>>> print(app.config.A)
1
```
````

.. 列:

```
此路径也接受基础风格环境变量。
```

.. 列:

````
```bash
$ export my_path="/path/to"
```
```python
app.update_config("${my_path}/my_config.py")
```
````

.. 注：

```
Just remember that you have to provide environment variables in the format `${environment_variable}` and that `$environment_variable` is not expanded (is treated as "plain" text).
```

#### 从一个词典

.. 列:

```
`app.update_config` 方法也适用于普通字典。
```

.. 列:

````
```python
app.update_config({"A": 1, "B": 2})
```
````

#### 来自类或对象

.. 列:

```
您可以定义自己的配置类，然后传递到 `app.update_config`
```

.. 列:

````
```python
class MyConfig:
    A = 1
    B = 2

app.update_config(MyConfig)
```
````

.. 列:

```
它甚至可以实例化。
```

.. 列:

````
```python
app.update_config(MyConfig())
```
````

### 铸造类型

当从环境变量加载时，Sanic会试图将这些值投射到预期的 Python 类型。 这尤其适用于：

- `int`
- `float`
- `bool`

关于“布尔值”，允许以下_case insensitive_value：

- **`True`**: `y`, `yes`, `yep`, `yup`, `t`, `true`, `on`, `enable`, `enabled`, `1`
- **`False`**: `n`, `no`, `false`, `off`, `disabled`, `0`

如果一个值不能投递，它将默认投递到一个 `str`。

.. 列:

```
此外，Sanic可以配置为使用其他类型转换器投射额外类型。 这应该是返回值或提升`ValueError`的任何可调用。

*添加于v21.12*
```

.. 列:

````
```python
app = Sanic(..., config=Config(converters=[UUID]))
```
````

## 内置值

| **变量**                                                                                 | **默认**    | **描述**                                                                          |
| -------------------------------------------------------------------------------------- | --------- | ------------------------------------------------------------------------------- |
| ACCESS_LOG                                                        | 真的        | 禁用或启用访问日志                                                                       |
| AUTO_EXTEND                                                       | 真的        | 控制 [Sanic Extensions](../../plugins/sanic-ext/getting-started.md) 是否会在现有虚拟环境中加载 |
| AUTO_RELOAD                                                       | 真的        | 控制文件更改时应用程序是否会自动重新加载                                                            |
| EVENT_AUTOREGISTER                                                | 真的        | 当`True`使用`app.event()`方法在不存在的信号上将自动创建它，而不会引起异常                                  |
| FALLBACK_ERROR_FORMAT                        | .html     | 未捕获和处理异常时的错误响应格式                                                                |
| FORWARDED_FOR_HEADER                         | X-转发-输入   | 包含客户端和代理IP的 "X-Forwarded-for" HTTP 头名称                                          |
| FORWARDED_SECRET                                                  | 无         | 用于安全识别特定代理服务器(见下文)                                           |
| GRACEFUL_SHUTDOWN_TIMEOUT                    | 15.0      | 强制关闭非空闲连接等待多长时间 (秒)                                          |
| INSPECTO                                                                               | 错误        | 是否启用检查器                                                                         |
| INSPECTOR_HOST                                                    | 本地主机      | 检查专员的主机                                                                         |
| INSPECTOR_PORT                                                    | 6457      | 检查员的端口                                                                          |
| INSPECTOR_TLS_TITLE                          | -         | 检查员的TLS密钥                                                                       |
| INSPECTOR_TLS_CERT                           | *         | 检查员的TLS证书                                                                       |
| INSPECTOR_API_KEY                            | -         | 检查员的 API 密钥                                                                     |
| KEEP_ALIVEUT                                                      | 120       | 保持TCP连接打开多长时间(秒)                                             |
| KEEP_ALIVE                                                        | 真的        | False 时禁用保持生命值                                                                  |
| MOTD                                                                                   | 真的        | 启动时是否显示 MOTD (当天消息)                                          |
| MOTD_DISPLAY                                                      | {}        | Key/value 对应显示额外的任意数据                                                           |
| NOISY_EXCEPTIONS                                                  | 错误        | 强制所有“安静”异常被记录                                                                   |
| PROXIES _COUNT                                                    | 无         | 在应用程序前面的代理服务器数量 (例如，nginx；见下方)                               |
| VIP_HEADER                                                        | 无         | 包含真实客户端IP的 "X-Real-IP" HTTP 头名称                                                 |
| 注册                                                                                     | 真的        | 是否启用应用注册                                                                        |
| REQUEST_BUFFER_SIZE                          | 65536     | 请求暂停前请求缓冲区大小，默认是 64 Kib                                                         |
| REQUEST_HEADER                                                    | X-请求-ID   | 包含请求/关联ID的 "X-Request-ID" HTTP 头名称                                              |
| REQUEST_MAX_SIZE                             | 100000000 | 请求的大小可能是 (bytes), 默认是 100 megabytes                          |
| REQUEST_MAX_HEADER_SIZE | 8192      | 请求头可能有多大(字节)，默认值为8192字节                                      |
| REQUEST_TIMEOUT                                                   | 60        | 到达请求可能需要多长时间(秒)                                              |
| 重置_TIMEOUT                                                        | 60        | 处理过程可能需要多长时间(秒)                                              |
| USE_UVLOOP                                                        | 真的        | 是否覆盖循环策略使用 `uvloop` 。 只支持 `app.run` 。                                           |
| WEBSOCKET_MAX_SIZE                           | 2^20      | 收到消息的最大大小(字节)                                                |
| WEBSOCKET_INTERVAL                                                | 20        | 每个ping_interval 秒都会发送一个Ping 帧。                             |
| WEBSOCKET_PING_TIMEOUT                       | 20        | 当Pong在ping_timeout秒后未收到时，连接将被关闭                            |

.. tip:: FYI

```
- The `USE_UVLOOP` value will be ignored if running with Gunicorn. Defaults to `False` on non-supported platforms (Windows).
- The `WEBSOCKET_` values will be ignored if in ASGI mode.
- v21.12 added: `AUTO_EXTEND`, `MOTD`, `MOTD_DISPLAY`, `NOISY_EXCEPTIONS`
- v22.9 added: `INSPECTOR`
- v22.12 added: `INSPECTOR_HOST`, `INSPECTOR_PORT`, `INSPECTOR_TLS_KEY`, `INSPECTOR_TLS_CERT`, `INSPECTOR_API_KEY`
```

## 超时

### REQUEST_TIMEOUT

请求超时测量当一个新打开的 TCP 连接传递到
Sanic 后端服务器时本机之间的时间长度。 和收到整个HTTP请求时的即时通讯。 如果所需时间超过
`REQUEST_TIMEOUT` (秒), 这被视为客户端错误，所以Sanic生成一个 `HTTP 408` 响应
并将其发送到客户端。 Set this parameter's value higher if your clients routinely pass very large request payloads
or upload requests very slowly.

### 重置_TIMEOUT

响应超时量度介于 Sanic 服务器通过 HTTP 请求到 Sanic App之间的时间。 即时HTTP响应发送到客户端。 如果时间超过`RESPONSE_TIMEOUT` (秒), 这被视为服务器错误，所以Sanic生成一个 `HTTP 503` 响应，并将其发送到客户端。 如果您的应用程序可能有长期运行的过程会延迟
生成响应，则设置此参数的值更高。

### KEEP_ALIVEUT

#### 什么是继续存活？ 保持活的超时值是什么？

`Keep-Alive`是`HTTP 1.1`中引入的HTTP功能。 发送 HTTP 请求时 客户端(通常是一个网页浏览器应用程序)可以设置一个 `Keep-Alive` 头来指示http服务器(Sanic)在发送响应后不关闭TCP连接。 这允许客户端重新使用现有的 TCP 连接来发送其后的 HTTP 请求。 并确保客户端和服务器更有效的网络通信。

默认情况下，`KEEP_ALIVE`配置变量设置为 `True`。 如果您在应用程序中不需要此功能， 设置为 `False` 以使所有客户端连接在响应发出后立即关闭。 无论请求时是否有“Keep-Alive”标题。

服务器保持TCP连接打开的时间长度由服务器自己决定。 在Sanic中，该值使用`KEEP_ALIVE_TIMEOUT` 来配置它。 默认情况下，**它被设置为 120 秒**。 这意味着，如果客户端发送一个 `Keep-Alive` 头，在发送响应后，服务器将保持TCP 连接打开120秒。 并且客户端可以在此时间内重新使用连接发送另一个 HTTP 请求。

供参考：

- Apache httpd 服务器默认保留生命超时 = 5 秒
- Nginx 服务器默认保留存活超时 = 75 秒
- Nginx 性能调节准则使用了保持生命=15秒
- Caddy 服务器默认保留存活超时 = 120秒
- IE (5-9) 客户硬保留生命限制 = 60 秒
- Firefox 客户硬存活限制 = 115秒
- Opera 11 客户端硬存活限制 = 120 秒
- Chrome 13+ 客户端保持生命限制 > 300+ 秒

## 代理配置

请参阅[代理配置部分](/guide/advanced/proxy-headers.md)
