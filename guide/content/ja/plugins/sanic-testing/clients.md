---
title: サニックテスト - テストクライアント
---

# クライアントのテスト

3つの異なるテストクライアントが用意されており、それぞれが異なる機能を提供します。

## 定期的な同期クライアント: `SanicTestClient`

`SanicTestClient` はローカルネットワーク上で実際のバージョンの Sanic Server を実行し、テストを実行します。 エンドポイントを呼び出すたびに、アプリケーションのバージョンを起動し、ホスト OS 上のソケットにバインドします。 次に、そのアプリケーションへ直接呼び出しを行うために `httpx` を使用します。

これは、Sanicアプリケーションがテストされる典型的な方法です。

.. 列::

```
Sanic Testing をインストールすると、通常の `SanicTestClient` をセットアップせずに使用できます。 これは、サニックがフードの下であなたのために脚を動作させるからです。 
```

.. 列::

````
```python
app.test_client.get("/path/to/endpoint")
```
````

.. 列::

```
しかし、クライアントを自分でインスタンス化することが望ましいと思うかもしれません。
```

.. 列::

````
```python
from sanic_testing.testing import SanicTestClient

test_client = SanicTestClient(app)
test_client.get("/path/to/endpoint")
```
````

.. 列::

```
テストクライアントを開始するための3つ目のオプションは、`TestManager` を使用することです。 これは、`SanicTestClient` と `SanicASGITestClient` の両方を設定する便利なオブジェクトです。
```

.. 列::

````
```python
from sanic_testing import TestManager

mgr = TestManager(app)
app.test_client.get("/path/to/endpoint")
# or
mgr.test_client.get("/path/to/endpoint")
```
````

以下のいずれかの方法でリクエストを行うことができます。

- `SanicTestClient.get`
- `SanicTestClient.post`
- `SanicTestClient.put`
- `SanicTestClient.patch`
- `SanicTestClient.delete`
- `SanicTestClient.options`
- `SanicTestClient.head`
- `SanicTestClient.websocket`
- `SanicTestClient.request`

これらのメソッドは `httpx` を使用するときとほぼ同じように使うことができます。 `httpx`に渡す引数は、**ひとつの注意を払って**以下のように受け入れられます: `test_clientを使用している場合。 equest`とHTTPメソッドを手動で指定したい場合は、`http_method`を使用してください。

```python
test_client.request("/path/to/endpoint", http_method="get")
```

## ASGI async client: `SanicASGITestClient`

リクエストごとにサーバーをスピンアップする `SanicTestClient` とは異なり、`SanicASGITestClient` はありません。 代わりに、`httpx`ライブラリを使用して、SanicをASGIアプリケーションとして実行し、ルートハンドラにアクセスして実行します。

.. 列::

```
このテストクライアントは全ての同じメソッドを提供し、一般的には `SanicTestClient` として動作します。 唯一の違いは、呼び出しごとに`await`を追加する必要があることです。
```

.. 列::

````
```python
await app.test_client.get("/path/to/endpoint")
```
````

`SanicASGITestClient` は `SanicTestClient` と全く同じ3つの方法で使用できます。

.. note::

```
`SanicASGITestClient` は ASGI アプリケーションでのみ使用する必要はありません。 `SanicTestClient` は同期エンドポイントのみをテストする必要がないのと同じ方法です。どちらのクライアントも、*任意*のSanicアプリケーションをテストすることができます。
```

## 永続的なサービスクライアント: `ReusableClient`

このクライアントは `SanicTestClient` と同様の前提で動作し、アプリケーションのインスタンスを立ち上げ、実際の HTTP リクエストを行います。 しかし、`SanicTestClient` とは異なり、`ReusableClient` を使用する場合は、アプリケーションのライフサイクルを制御します。

つまり、リクエストごとに**新しいWebサーバーを起動しません**。 代わりに、サーバーを起動し、必要に応じて停止し、同じ実行中のインスタンスに複数のリクエストを行うことができます。

.. 列::

```
他の2つのクライアントとは異なり、このクライアントを**インスタンス化**して使用する必要があります：
```

.. 列::

````
```python
from sanic_testing.reusable import ReusableClient

client = ReusableClient(app)
```
````

.. 列::

```
作成されると、コンテキストマネージャーの内部のクライアントを使用します。マネージャーの範囲外の場合、サーバーはシャットダウンします。
```

.. 列::

````
```python
from sanic_testing.reusable import ReusableClient

def test_multiple_endpoints_on_same_server(app):
    client = ReusableClient(app)
    with client:
        _, response = client.get("/path/to/1")
        assert response.status == 200

        _, response = client.get("/path/to/2")
        assert response.status == 200
```
````
