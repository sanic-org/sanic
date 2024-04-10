# 代理配置 (Proxy configuration)

当您使用反向代理服务器（例如nginx）时，`request.ip` 的值将包含代理的IP地址，通常是 `127.0.0.1`。 几乎在所有情况下，这都不是您所期望得到的结果。

Sanic 可以配置为使用代理头信息来确定真实的客户端IP地址，该地址可通过 `request.remote_addr` 获取。 如果有提供的话，完整的外部URL也会从头字段中构建出来。

.. tip:: 注意一下

```
未经适当防护措施，恶意客户端可能会利用代理头信息伪造自己的IP地址。为了避免这类问题，Sanic默认不使用任何代理头信息，除非明确启用此功能。
```

.. column::

```
部署在反向代理之后的服务必须配置以下[配置值](/zh/guide/deployment/configuration.md)之一或多者：

- `FORWARDED_SECRET`
- `REAL_IP_HEADER`
- `PROXIES_COUNT`
```

.. column::

````
```python
app.config.FORWARDED_SECRET = "super-duper-secret"
app.config.REAL_IP_HEADER = "CF-Connecting-IP"
app.config.PROXIES_COUNT = 2
```
````

## 转发头(Forwarded header)

为了使用“Forwarded”头信息，您应该将 `app.config.FORWARDED_SECRET` 设置为可信代理服务器所知的一个值。 这个密钥用于安全地识别特定的代理服务器。

如果没有设置密钥，Sanic会忽略任何没有密钥的秘密元素，甚至不会解析该头信息。

一旦找到可信的转发元素，所有其他代理头信息都将被忽略，因为可信的转发元素已经携带了关于客户端的完整信息。

要了解更多关于Forwarded头信息的内容，请阅读相关的 [MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Forwarded) 和[Nginx](https://www.nginx.com/resources/wiki/start/topics/examples/forwarded/) 文章。

## 常见的代理请求头(Traditional proxy headers)

### IP Headers

当您的代理通过某个已知头信息传递IP地址时，您可以使用 `REAL_IP_HEADER` 配置值告诉Sanic这个头信息是什么。

### X-Forwarded-For

此头信息通常包含经过每一层代理的IP地址链。 设置 PROXIES_COUNT 告诉Sanic应深入到哪一层以获取实际的客户端IP地址。 这个值应等于链中IP地址预期的数量。

### Other X-headers

如果通过上述方法找到了客户端IP地址，Sanic会使用以下头信息来构建URL各部分：

- x-forwarded-proto
- x-forwarded-host
- x-forwarded-port
- x-forwarded-path
- x-scheme

## 示例

在以下示例中，所有请求都将以如下形式的路由入口为基础进行演示：

```python
@app.route("/fwd")
async def forwarded(request):
    return json(
        {
            "remote_addr": request.remote_addr,
            "scheme": request.scheme,
            "server_name": request.server_name,
            "server_port": request.server_port,
            "forwarded": request.forwarded,
        }
    )
```

---

##### 例一(Example 1)

若未配置`FORWARDED_SECRET`，应尊重x-headers

```sh
curl localhost:8000/fwd \
	-H 'Forwarded: for=1.1.1.1, for=injected;host=", for="[::2]";proto=https;host=me.tld;path="/app/";secret=mySecret,for=broken;;secret=b0rked, for=127.0.0.3;scheme=http;port=1234' \
	-H "X-Real-IP: 127.0.0.2" \
	-H "X-Forwarded-For: 127.0.1.1" \
	-H "X-Scheme: ws" \
	-H "Host: local.site" | jq
```

.. column::

````
```python
# Sanic application config
app.config.PROXIES_COUNT = 1
app.config.REAL_IP_HEADER = "x-real-ip"
```
````

.. column::

````
```bash
# curl response
{
  "remote_addr": "127.0.0.2",
  "scheme": "ws",
  "server_name": "local.site",
  "server_port": 80,
  "forwarded": {
    "for": "127.0.0.2",
    "proto": "ws"
  }
}
```
````

---

##### 例二(Example 2)

`FORWARDED_SECRET` 已配置

```sh
curl localhost:8000/fwd \
	-H 'Forwarded: for=1.1.1.1, for=injected;host=", for="[::2]";proto=https;host=me.tld;path="/app/";secret=mySecret,for=broken;;secret=b0rked, for=127.0.0.3;scheme=http;port=1234' \
	-H "X-Real-IP: 127.0.0.2" \
	-H "X-Forwarded-For: 127.0.1.1" \
	-H "X-Scheme: ws" \
	-H "Host: local.site" | jq
```

.. column::

````
```python
# Sanic application config
app.config.PROXIES_COUNT = 1
app.config.REAL_IP_HEADER = "x-real-ip"
app.config.FORWARDED_SECRET = "mySecret"
```
````

.. column::

````
```bash
# curl response
{
  "remote_addr": "[::2]",
  "scheme": "https",
  "server_name": "me.tld",
  "server_port": 443,
  "forwarded": {
    "for": "[::2]",
    "proto": "https",
    "host": "me.tld",
    "path": "/app/",
    "secret": "mySecret"
  }
}
```
````

---

##### 例三(Example 3)

空`Forwarded`头信息 -> 使用`X-headers`

```sh
curl localhost:8000/fwd \
	-H "X-Real-IP: 127.0.0.2" \
	-H "X-Forwarded-For: 127.0.1.1" \
	-H "X-Scheme: ws" \
	-H "Host: local.site" | jq
```

.. column::

````
```python
# Sanic application config
app.config.PROXIES_COUNT = 1
app.config.REAL_IP_HEADER = "x-real-ip"
app.config.FORWARDED_SECRET = "mySecret"
```
````

.. column::

````
```bash
# curl response
{
  "remote_addr": "127.0.0.2",
  "scheme": "ws",
  "server_name": "local.site",
  "server_port": 80,
  "forwarded": {
    "for": "127.0.0.2",
    "proto": "ws"
  }
}
```
````

---

##### 例四(Example 4)

存在头信息但无法匹配任何内容

```sh
curl localhost:8000/fwd \
	-H "Forwarded: nomatch" | jq
```

.. column::

````
```python
# Sanic application config
app.config.PROXIES_COUNT = 1
app.config.REAL_IP_HEADER = "x-real-ip"
app.config.FORWARDED_SECRET = "mySecret"
```
````

.. 列:

````
```bash
# curl response
{
  "remote_addr": "",
  "scheme": "http",
  "server_name": "localhost",
  "server_port": 8000,
  "forwarded": {}
}

```
````

---

##### 例五(Example 5)

`Forwarded`头信息存在，但无匹配的密钥 -> 使用`X-headers`

```sh
curl localhost:8000/fwd \
	-H "Forwarded: for=1.1.1.1;secret=x, for=127.0.0.1" \
	-H "X-Real-IP: 127.0.0.2" | jq
```

.. column::

````
```python
# Sanic application config
app.config.PROXIES_COUNT = 1
app.config.REAL_IP_HEADER = "x-real-ip"
app.config.FORWARDED_SECRET = "mySecret"
```
````

.. column::

````
```bash
# curl response
{
  "remote_addr": "127.0.0.2",
  "scheme": "http",
  "server_name": "localhost",
  "server_port": 8000,
  "forwarded": {
    "for": "127.0.0.2"
  }
}
```
````

---

##### 例六(Example 6)

不同格式化方式，同时触及头信息两端的情况

```sh
curl localhost:8000/fwd \
	-H 'Forwarded: Secret="mySecret";For=127.0.0.4;Port=1234' | jq
```

.. column::

````
```python
# Sanic application config
app.config.PROXIES_COUNT = 1
app.config.REAL_IP_HEADER = "x-real-ip"
app.config.FORWARDED_SECRET = "mySecret"
```
````

.. column::

````
```bash
# curl response
{
  "remote_addr": "127.0.0.4",
  "scheme": "http",
  "server_name": "localhost",
  "server_port": 1234,
  "forwarded": {
    "secret": "mySecret",
    "for": "127.0.0.4",
    "port": 1234
  }
}
```
````

---

##### 例七(Example 7)

测试转义字符（如果发现有人实现引用对，请修改此处）

```sh
curl localhost:8000/fwd \
	-H 'Forwarded: for=test;quoted="\,x=x;y=\";secret=mySecret' | jq
```

.. column::

````
```python
# Sanic application config
app.config.PROXIES_COUNT = 1
app.config.REAL_IP_HEADER = "x-real-ip"
app.config.FORWARDED_SECRET = "mySecret"
```
````

.. column::

````
```bash
# curl response
{
  "remote_addr": "test",
  "scheme": "http",
  "server_name": "localhost",
  "server_port": 8000,
  "forwarded": {
    "for": "test",
    "quoted": "\\,x=x;y=\\",
    "secret": "mySecret"
  }
}
```
````

---

##### 例八(Example 8)

密钥信息因格式错误的字段而被隔绝 #1

```sh
curl localhost:8000/fwd \
	-H 'Forwarded: for=test;secret=mySecret;b0rked;proto=wss;' | jq
```

.. column::

````
```python
# Sanic application config
app.config.PROXIES_COUNT = 1
app.config.REAL_IP_HEADER = "x-real-ip"
app.config.FORWARDED_SECRET = "mySecret"
```
````

.. column::

````
```bash
# curl response
{
  "remote_addr": "test",
  "scheme": "http",
  "server_name": "localhost",
  "server_port": 8000,
  "forwarded": {
    "for": "test",
    "secret": "mySecret"
  }
}
```
````

---

##### 例九(Example 9)

密钥信息因格式错误的字段而被隔绝 #2

```sh
curl localhost:8000/fwd \
	-H 'Forwarded: for=test;b0rked;secret=mySecret;proto=wss' | jq
```

.. column::

````
```python
# Sanic application config
app.config.PROXIES_COUNT = 1
app.config.REAL_IP_HEADER = "x-real-ip"
app.config.FORWARDED_SECRET = "mySecret"
```
````

.. column::

````
```bash
# curl response
{
  "remote_addr": "",
  "scheme": "wss",
  "server_name": "localhost",
  "server_port": 8000,
  "forwarded": {
    "secret": "mySecret",
    "proto": "wss"
  }
}
```
````

---

##### 例十(Example 10)

意外终止不应丢失现有的有效值

```sh
curl localhost:8000/fwd \
	-H 'Forwarded: b0rked;secret=mySecret;proto=wss' | jq
```

.. column::

````
```python
# Sanic application config
app.config.PROXIES_COUNT = 1
app.config.REAL_IP_HEADER = "x-real-ip"
app.config.FORWARDED_SECRET = "mySecret"
```
````

.. column::

````
```bash
# curl response
{
  "remote_addr": "",
  "scheme": "wss",
  "server_name": "localhost",
  "server_port": 8000,
  "forwarded": {
    "secret": "mySecret",
    "proto": "wss"
  }
}
```
````

---

##### 例十一(Example 11)

字段标准化

```sh
curl localhost:8000/fwd \
	-H 'Forwarded: PROTO=WSS;BY="CAFE::8000";FOR=unknown;PORT=X;HOST="A:2";PATH="/With%20Spaces%22Quoted%22/sanicApp?key=val";SECRET=mySecret' | jq
```

.. column::

````
```python
# Sanic application config
app.config.PROXIES_COUNT = 1
app.config.REAL_IP_HEADER = "x-real-ip"
app.config.FORWARDED_SECRET = "mySecret"
```
````

.. column::

````
```bash
# curl response
{
  "remote_addr": "",
  "scheme": "wss",
  "server_name": "a",
  "server_port": 2,
  "forwarded": {
    "proto": "wss",
    "by": "[cafe::8000]",
    "host": "a:2",
    "path": "/With Spaces\"Quoted\"/sanicApp?key=val",
    "secret": "mySecret"
  }
}
```
````

---

##### 例十二(Example 12)

使用 "by" 字段作为密钥

```sh
curl localhost:8000/fwd \
	-H 'Forwarded: for=1.2.3.4; by=_proxySecret' | jq
```

.. column::

````
```python
# Sanic application config
app.config.PROXIES_COUNT = 1
app.config.REAL_IP_HEADER = "x-real-ip"
app.config.FORWARDED_SECRET = "_proxySecret"
```
````

.. column::

````
```bash
# curl response
{
  "remote_addr": "1.2.3.4",
  "scheme": "http",
  "server_name": "localhost",
  "server_port": 8000,
  "forwarded": {
    "for": "1.2.3.4",
    "by": "_proxySecret"
  }
}

```
````
