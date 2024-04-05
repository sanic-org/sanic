---
title: TLS/SSL/HTTPS
---

# TLS/SSL/HTTPS

> HTTPS経由でSanicを実行するにはどうすればよいですか?

まだ TLS 証明書を持っていない場合は、format@@0(./tls.md#get-certificates-for-your-domain-names) を参照してください。

## 単一ドメインと単一証明書

.. 列::

```
Sanicに指定されたフォルダに`fullchain.pem`と`privkey.pem`という名前の証明書ファイルを自動的にロードさせます：
```

.. 列::

````
```sh
sudo sanic myserver:app -H :: -p 443 \
  --tls /etc/letsencrypt/live/example.com/
```
```python
app.run("::", 443, ssl="/etc/letsencrypt/live/example.com/")
```
````

.. 列::

```
または、certとキーファイル名を辞書として個別に渡すこともできます:

キーが暗号化されている場合は、パスワードを除くすべてのフィールドが `request` に追加されます。 on_info.cert`
```

.. 列::

````
```python
ssl = {
    "cert": "/path/to/fullchain.pem",
    "key": "/path/to/privkey.pem",
    "password": "for encrypted privkey file",   # Optional
}
app.run(host="0.0.0.0", port=8443, ssl=ssl)
```
````

.. 列::

```
代わりに、[`ssl.SSLContext`](https://docs.python.org/3/library/ssl.html)が渡されます。どの暗号アルゴリズムが許可されているかなど、詳細を完全に制御する必要がある場合。 デフォルトでは、Sanicはセキュアなアルゴリズムのみを許可し、これは非常に古いデバイスからのアクセスを制限する可能性があります。
```

.. 列::

````
```python
import ssl

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain("certs/fullchain.pem", "certs/privkey.pem")

app.run(host="0.0.0.0", port=8443, ssl=context)
```
````

## 別の証明書を持つ複数のドメイン

.. 列::

```
複数の証明書のリストを提供することができます。その場合、Sanic はユーザーが接続しているホスト名に一致するものを選択します。 これは TLS ハンドシェイクの早い段階で発生し、Sanic はまだクライアントにパケットを送信していない。

クライアントがSNI(サーバー名表示)を送信していない場合 リストの最初の証明書は、クライアントブラウザ上で名前が一致しないため、TLS エラーで失敗する可能性がありますが使用されます。 このフォールバックを防ぎ、既知のホスト名なしでクライアントの接続を即座に切断するには、リストの最初のエントリとして `None` を追加します。 `--tls-strict-host` はCLIオプションと同等です。
```

.. 列::

````
```python
ssl = ["certs/example.com/", "certs/bigcorp.test/"]
app.run(host="0.0.0.0", port=8443, ssl=ssl)
```
```sh
sanic myserver:app
    --tls certs/example.com/
    --tls certs/bigcorp.test/
    --tls-strict-host
```
````

.. tip::

```
証明書を公開したくない場合は、1つの証明書の前に `None` を使用することもできます。 適切なDNS名ではなく、IPアドレスに接続している人への真のホスト名またはサイトコンテンツ。
```

.. 列::

```
辞書はリストで使用できます。 これにより、証明書が一致するドメインを指定することができますが、証明書自体に存在する名前は、ここから制御することはできません。 names が指定されていない場合、証明書自体からの名前が使用されます。

メインドメイン **example.com** とサブドメインのみ **bigcorp.test** への接続を許可するには:
```

.. 列::

````
```python
ssl = [
    None,  # No fallback if names do not match!
    {
        "cert": "certs/example.com/fullchain.pem",
        "key": "certs/example.com/privkey.pem",
        "names": ["example.com", "*.bigcorp.test"],
    }
]
app.run(host="0.0.0.0", port=8443, ssl=ssl)
```
````

## `request.conn_info` フィールドを介してハンドラ内の TLS 情報にアクセスする

- `.ssl` - 接続セキュア (bool)
- `.cert` - 現在アクティブな証明書の情報とdict フィールド (dict)
- `.server_name` - クライアントによって送信されたSNI（str、空かもしれない）

すべての `conn_info` フィールドは接続ごとに存在し、時間の経過とともに多くのリクエストがあることに注意してください。 プロキシがサーバの前で使用されている場合、同じパイプでのこれらのリクエストは異なるユーザからのものでもあります。

## HTTPをHTTPSにリダイレクトし、証明書要求は引き続きHTTP経由で行われます

HTTPS が実行されている通常のサーバーに加えて、`http_redir.py`をリダイレクトする別のサーバーを実行します。

```python
from sanic import Sanic, exceptions, response

app = Sanic("http_redir")

# Serve ACME/certbot files without HTTPS, for certificate renewals
app.static("/.well-known", "/var/www/.well-known", resource_type="dir")

@app.exception(exceptions.NotFound, exceptions.MethodNotSupported)
def redirect_everything_else(request, exception):
    server, path = request.server_name, request.path
    if server and path.startswith("/"):
        return response.redirect(f"https://{server}{path}", status=308)
    return response.text("Bad Request. Please use HTTPS!", status=400)
```

HTTPS サーバーとは別の systemd ユニットとしてセットアップするのが最善です。 HTTPSサーバーはまだ実行できませんが、最初に証明書をリクエストする際にHTTPを実行する必要がある場合があります。 IPv4とIPv6の起動:

```
sanic http_redir:app -H 0.0.0.0 -p 80
sanic http_redir:app -H :: -p 80
```

または、メインアプリケーションからHTTPリダイレクトアプリケーションを実行することもできます。

```python
# app == Your main application
# redirect == Your http_redir application
@app.before_server_start
async def start(app, _):
    app.ctx.redirect = await redirect.create_server(
        port=80, return_asyncio_server=True
    )
    app.add_task(runner(redirect, app.ctx.redirect))

@app.before_server_stop
async def stop(app, _):
    await app.ctx.redirect.close()

async def runner(app, app_server):
    app.state.is_running = True
    try:
        app.signalize()
        app.finalize()
        app.state.is_started = True
        await app_server.serve_forever()
    finally:
        app.state.is_running = False
        app.state.is_stopping = True
```

## ドメイン名の証明書を取得する

format@@0(https://letsencrypt.org/)から無料で証明書を取得できます。 パッケージマネージャーから [certbot](https://certbot.eff.org/) をインストールし、証明書を要求します。

```sh
sudo certbot certonly --key-type ecdsa --preferred-chain "ISRG Root X1" -d example.com -d www.example.com
```

複数のドメイン名は `-d` 引数によって追加されることができます。すべてが `/etc/letsencrypt/live/example` に保存される単一の証明書に格納されます。 ここにリストされている**最初のドメイン**に従って、om/\`。

キータイプと優先チェーンオプションは、最小サイズの証明書ファイルを取得するために必要です。 サーバーをできるだけ速く動作させるために不可欠です。 このチェーンには、Let's Encryptがすべての主要なブラウザで新しいECチェーンを信頼するまで、1つのRSA証明書が含まれます。
