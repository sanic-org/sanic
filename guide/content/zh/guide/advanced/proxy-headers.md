# 代理配置

当您使用反向代理服务器 (例如nginx) 时，`request.ip` 的值将包含代理的 IP，通常是 `127.0.0.1` 。 几乎总是**不是**你想要的。

Sanic 可能被配置为使用代理头来确定真正的客户端 IP，可用于“request.remote_addr”。 完整的外部 URL 也是从标题字段 _如果可用的话_构建的。

.. 提示：浮动通知

```
如果没有适当的防范措施，恶意客户可能会使用代理头来歪曲自己的IP。 为了避免这种问题，除非明确启用，否则Sanic不会使用任何代理标题。
```

.. 列:

```
逆向代理后面的服务必须配置以下[配置值](/guide/deplement/configuration.md):

- `FORWARDED_SECRET`
- `REAL_IP_HEADER`
- `PROXIES_COUNT`
```

.. 列:

````
```python
app.config.FORWARDED_SECRET = "超级duper-secret"
app.config.REAL_IP_HEADER = "CF-Connecting-IP"
app.config.PROXIEs_COUNT = 2
```
````

## 转发标题

为了使用 `Forwarded` 标题，您应该将 `app.config.FORWARDED_SECRET` 设置为信任的代理服务器已知的值。 此密钥用于安全识别特定代理服务器。

神秘忽略任何没有密钥的元素，如果没有设置秘密，甚至不会解析标题。

所有其它代理头在找到可信任的转发元素时被忽略，因为它已经包含了有关客户端的完整信息。

若要了解更多关于 `Forwarded` 标题，请阅读相关的 [MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Forwarded) 和 [Nginx](https://www.nginx.com/resources/wiki/start/topics/examples/forwarded/) 文章。

## 传统代理信头

### IP 头

当你的代理转发你已知的标题中的 IP 地址时，你可以告诉Sanic 什么是 `REAL_IP_HEADER` 配置值。

### X-转发-输入

此页眉通常包含一个通过代理服务器的每层IP地址链。 设置 `PROXIES_COUNT` 告诉Sanic寻找客户端的实际IP地址。 此值应等于 _expected_number 的 IP 地址。

### 其他X-headers

如果客户端IP找到这些方法之一，Sanic对URL部分使用以下标题：

- x-转发-proto
- x转发主机
- x转发端口
- x转发路径
- x 方案

## 示例：

在下面的例子中，所有请求都将假定终点看起来像这样：

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

##### 例1

如果没有配置FORWARDED_SECRET, X-headers 应该受到尊重。

```sh
curl localhost:8000/fwd \
	-H 'Forwar: for=1.1.1, for=injected;host="[:2]";proto=https://;host=me.tld;path="/app/";secret=mySecret,for=brochen;secret=b0rked, for=127。 .0.3;scheme=http;port=1234' \
	-H "X-Real-IP: 127.0.0.2"
	-H "X-For: 127.0.1"
	- H "X-Scheme: w"
	- H "Host: local.site" | jq
```

.. 列:

````
```python
# Sanic application config
app.config.PROXIES_COUNT = 1
app.config.REAL_IP_HEADER = "x-real-ip"
```
````

.. 列:

````
```bash
# curl replacement
Paper
  "remote_addr": "127.0.0.0.2",
  "scheme": "ws",
  "server_name": "local. ite”,
  "server_port": 80,
  "forwarded": 许诺,
    "for": "127. .0.2",
    "proto": "ws"
  }
}
```
````

---

##### 例2

FORWARDED_SECRET 已配置

```sh
curl localhost:8000/fwd \
	-H 'Forwar: for=1.1.1, for=injected;host="[:2]";proto=https://;host=me.tld;path="/app/";secret=mySecret,for=brochen;secret=b0rked, for=127。 .0.3;scheme=http;port=1234' \
	-H "X-Real-IP: 127.0.0.2"
	-H "X-For: 127.0.1"
	- H "X-Scheme: w"
	- H "Host: local.site" | jq
```

.. 列:

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

##### 例3

空转发头 -> 使用 X-headers

```sh
curl localhost:8000/fwd \
	-H "X-Real-IP: 127.0.0.2" \
	-H "X-For: 127.0.1" \
	-H "X-Scheme: w"
	-H "Host: local.site" | jq
```

.. 列:

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
# curl replacement
Paper
  "remote_addr": "127.0.0.0.2",
  "scheme": "ws",
  "server_name": "local. ite”,
  "server_port": 80,
  "forwarded": 许诺,
    "for": "127. .0.2",
    "proto": "ws"
  }
}
```
````

---

##### 例4

页眉已存在，但不匹配任何内容

```sh
curl localhost:8000/fwd \
	-H "Forwar: nomatch" | jq
```

.. 列:

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
Power
  "remote_addr": "",
  "scheme": "http",
  "server_name": "localhost",
  "server_port": 8000,
  "forwarded": {}
}

```
````

---

##### 例5

转发头，但没有匹配的密钥 -> 使用 X-headers

```sh
curl localhost:8000/fwd \
	-H "Forwar: for=1.1.1;secret=x, for=127.0.0.1"
	-H "X-Real-IP: 127.0.0.2" | jq
```

.. 列:

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
# curl reply
Power
  "remote_addr": "127.0.0.0 ",
  "scheme": "http",
  "server_name": "localhost",
  "server_port": 8000,
  "forwarded": 许诺,
    "for": "127. 0.2"
  }
}
```
````

---

##### 例6

不同格式化并击中标题两端的标题

```sh
curl localhost:8000/fwd \
	-H 'Forward: Secret="mysecret";For=127.0.0.4;Port=1234' | jq
```

.. 列:

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
# curl reply
Power
  "remote_addr": "127.0.0.0 ",
  "scheme": "http",
  "server_name": "localhost",
  "server_port": 1234,
  "forwarded": Power
    "secret": "mysecret",
    "for": "127. .0.4",
    "port": 1234
  }
}
```
````

---

##### 例7

测试逃逸(如果你看到有人正在执行引用的对等内容，请修改此选项)

```sh
curl localhost:8000/fwd \
	-H 'Forwar: for=test;quoted="\,x=x;y=\";secret=mysecret' | jq
```

.. 列:

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
# curl replacement
Paper
  "remote_addr": "test",
  "scheme": "http",
  "server_name": "localhost",
  "server_port": 8000,
  "forwarded": 许诺,
    "for": "test",
    "quoted": "\,x=x; =\\",
    "secret": "mysecret"
  }
}
```
````

---

##### 例8

由格式错误的字段 #1 隔绝的绝密项

```sh
curl localhost:8000/fwd \
	-H 'Forwar: for=test;secret=mySecret;b0rked;proto=wss;' | jq
```

.. 列:

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

##### 例9

由格式不正确的字段 #2 隔热绝的密钥

```sh
curl localhost:8000/fwd \
	-H 'Forwar: for=test;b0rked;secret=mySecret;proto=wss' | jq
```

.. 列:

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
WP
  "remote_addr": "",
  "scheme": "wss",
  "server_name": "localhost",
  "server_port": 8000,
  "forwarded": 许诺
    "secret": "mysecret",
    "proto": "wss"
  }
}
```
````

---

##### 例10

意外终止不应丢失现有可接受的值

```sh
curl localhost:8000/fwd \
	-H 'Forwar: b0rked;secret=mySecret;proto=wss' | jq
```

.. 列:

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
WP
  "remote_addr": "",
  "scheme": "wss",
  "server_name": "localhost",
  "server_port": 8000,
  "forwarded": 许诺
    "secret": "mysecret",
    "proto": "wss"
  }
}
```
````

---

##### 例11

实地正常化

```sh
curl localhost:8000/fwd \
	-H 'Forwarded: PROTO=WSS;BY="CAFE::8000";FOR=unknown;PORT=X;HOST="A:2";PATH="/With%20Spaces%22Quoted%22/sanicApp?key=val";SECRET=mySecret' | jq
```

.. 列:

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
Power
  "remote_addr": "",
  "scheme": "wss",
  "server_name": "a",
  "server_port": 2,
  "转发": Power
    "原始": "wss",
    "by": "[cafe:8000]",
    "主机": "a:2",
    "路径": "/With Spaces\"Quoted\"/sanicApp? ey=val",
    "secret": "mysecret"
  }
}
```
````

---

##### 例12

使用“by”字段作为密钥

```sh
curl localhost:8000/fwd \
	-H 'Forward: for=1.2.3.4; by=_proxySecret' | jq
```

.. 列:

````
```python
# Sanic application config
app.config.PROXIES_COUNT = 1
app.config.REAL_IP_HEADER = "x-real-ip"
app.config.FORWARDED_SECRET = "_proxySecret"
```
````

.. 列:

````
```bash
# curl response
Power
  "remote_addr": "1.2.3。 ",
  "scheme": "http",
  "server_name": "localhost",
  "server_port": 8000,
  "forwarded": 许诺,
    "for": "1. .3.4",
    "by": "_proxySecret"
  }
}

```
````
