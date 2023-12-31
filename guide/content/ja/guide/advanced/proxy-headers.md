# プロキシ設定

リバースプロキシサーバー(nginxなど)を使用する場合、`request.ip`の値にはプロキシのIP(通常は`127.0.0.1`)が含まれます。 ほとんどの場合、これはあなたが望むもの**ではありません**。

Sanicは、`request.remote_addr`として利用可能な本当のクライアントIPを決定するためにプロキシヘッダーを使用するように構成できます。 完全な外部URLは、_使用できれば_ヘッダーフィールドからも構築されます。

.. tip:: ヒント

```
適切な予防措置がなければ、悪意のあるクライアントはプロキシヘッダーを使用して独自のIPを偽装することができます。このような問題を回避するために、Sanicは明示的に有効になっていない限り、プロキシヘッダーを使用しません。
```

.. column::

```
リバースプロキシを使うサービスは、次の[構成値](/guide/deployment/configuration.md)の1つ以上を設定する必要があります。

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

## Forwarded ヘッダー

`Forwarded`ヘッダーを使用するには、信頼できるプロキシサーバーに設定されている値を`app.config.FORWARDED_SECRET`に設定する必要があります。 このシークレットは、特定のプロキシサーバーを安全に識別するために使用されます。

Sanicはシークレットキーのない要素を無視し、シークレットが設定されていない場合はヘッダーを解析することもありません。

信頼された転送要素が見つかると、他のすべてのプロキシヘッダは無視されます。クライアントに関する完全な情報をすでに運んでいるからです。

`Forwarded`ヘッダーの詳細については、関連する[MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Forwarded)および[Nginx](https://www.nginx.com/resources/wiki/start/topics/examples/forwarded/)の記事を参照してください。(訳注: 両方とも英語です)

## 従来のプロキシヘッダー

### IP ヘッダー

プロキシが既知のヘッダーにIPアドレスを転送するとき`REAL_IP_HEADER`の値を指定すると、Sanicにそれが何かを教えることができます。

### X-Forwarded-For

このヘッダーには、通常、プロキシの各レイヤーを介したIPアドレスのチェーンが含まれています。 `PROXIES_COUNT`を設定すると、クライアントの実際のIPアドレスを取得する深さがSanicに指示されます。 この値は、チェーン内のIPアドレスの _期待される_ 数に等しいはずです。

### その他のXヘッダー

クライアントIPがこれらのメソッドのいずれかで見つかった場合、Sanicは以下のURLパーツのヘッダを使用します:

- x-forwarded-proto
- x-forwarded-host
- x-forwarded-port
- x-forwarded-path
- x-scheme

## 例

以下の例では、すべてのリクエストはエンドポイントが次のようになると仮定します。

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

***

##### 例1

FORWARDED_SECRETが設定されていない場合、Xヘッダは尊重されます。

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
# curlの応答
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

***

##### 例2

FORWARDED_SECRETが設定された場合

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
```curlの応答
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
```
````

***

##### 例3

空の転送ヘッダー - > Xヘッダーを使用する

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
# curlの応答
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

***

##### 例4

ヘッダーは存在するのに何も一致しない場合。

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

.. column::

````
```bash
# curlの応答
{
  "remote_addr": "",
  "scheme": "http",
  "server_name": "localhost",
  "server_port": 8000,
  "forwarded": {}
}

```
````

***

##### 例5

Forwarded ヘッダーは存在するが、一致するシークレットはない場合 -> Xヘッダを使用

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
# curlの応答
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

***

##### 例6

フォーマットが異なり、ヘッダーの両端がヒットする場合

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
# curlの応答
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

***

##### 例7

エスケープをテストする場合(quoted-pairsを実装しているのを見かけたら修正してあげてください)。

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
# curlの応答
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

***

##### Example 8

Secret insulated by malformed field #1

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

***

##### Example 9

Secret insulated by malformed field #2

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

***

##### Example 10

Unexpected termination should not lose existing acceptable values

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

***

##### Example 11

Field normalization

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

***

##### Example 12

Using "by" field as secret

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
