# Handlers

次に重要なビルディングブロックは _handlers_ です。 これらは"views"とも呼ばれます。

In Sanic, a handler is any callable that takes at least a :class:`sanic.request.Request` instance as an argument, and returns either an :class:`sanic.response.HTTPResponse` instance, or a coroutine that does the same.

.. 列::

```
Huh? 😕

It is a **function**; either synchronous or asynchronous.

The job of the handler is to respond to an endpoint and do something. This is where the majority of your business logic will go.
```

.. 列::

````
```python
def i_am_a_handler(request):
    return HTTPResponse()

async def i_am_ALSO_a_handler(request):
    return HTTPResponse()
```
````

さらに2つの重要な注意事項:

1. あなたは :class:`sanic.response.HTTPresponse` を直接使用したくないでしょう。 format@@0(./response#methods) のいずれかを使う方が簡単です。

   - `from sanic import json`
   - `from sanic import html`
   - `from sanic import redirect`
   - _etc_
2. format@@0(../advanced/streaming#response-streaming)で見るように、オブジェクトを返す必要はありません。 この下位レベルの API を使用する場合は、ハンドラ内からのレスポンスのフローを制御することができ、戻り値オブジェクトは使用されません。

.. tip:: Heads Up

```
ロジックのカプセル化についてもっと知りたい場合は、[class based views](../advanced/class-based-views.md) をチェックしてください。今後は関数ベースのビューだけで進めていきます。
```

### シンプルな関数ベースのハンドラです

ルートハンドラを作成する最も一般的な方法は、関数を飾ることです。 ルート定義の視覚的に簡単な識別を作成します。 format@@0(./routing.md) の詳細について学びます。

.. 列::

```
Let's look at a practical example.

- We use a convenience decorator on our app instance: `@app.get()`
- And a handy convenience method for generating out response object: `text()`

Mission accomplished 💪
```

.. 列::

````
```python
from sanic import text

@app.get("/foo")
async def foo_handler(request):
    return text("I said foo!")
```
````

***

## _async_についての単語。

.. 列::

```
It is entirely possible to write handlers that are synchronous.

In this example, we are using the _blocking_ `time.sleep()` to simulate 100ms of processing time. Perhaps this represents fetching data from a DB, or a 3rd-party website.

Using four (4) worker processes and a common benchmarking tool:

- **956** requests in 30.10s
- Or, about **31.76** requests/second
```

.. 列::

````
```python
@app.get("/sync")
def sync_handler(request):
    time.sleep(0.1)
    return text("Done")
```
````

.. 列::

```
Just by changing to the asynchronous alternative `asyncio.sleep()`, we see an incredible change in performance. 🚀

Using the same four (4) worker processes:

- **115,590** requests in 30.08s
- Or, about **3,843.17** requests/second

.. attrs::
    :class: is-size-2

    🤯
```

.. 列::

````
```python
@app.get("/async")
async def async_handler(request):
    await asyncio.sleep(0.1)
    return text("Done")
```
````

わかりました... これは途方もなく過大な結果です どんなベンチマークでも本質的に偏っています この例では、ウェブの世界での `async/await` の利点を紹介します。 結果は確かに異なります。 Sanicや他の非同期Pythonライブラリのようなツールは、物事をより速くする魔法の弾丸ではありません。 これらは _more efficient_ にします。

この例では、1つのリクエストがスリープ状態になっているため、非同期バージョンが非常に優れています。 別のものと別のものと別のものと別のものを始めることができます

しかし、これはポイントである! Sanicは利用可能なリソースを取り出し、パフォーマンスを絞り出すため、高速です。 同時に多くのリクエストを処理することができます。つまり、1秒あたりのリクエストが多くなります。

.. tip:: よくある間違い!

```
Don't do this! You need to ping a website. What do you use? `pip install your-fav-request-library` 🙈

Instead, try using a client that is `async/await` capable. Your server will thank you. Avoid using blocking tools, and favor those that play well in the asynchronous ecosystem. If you need recommendations, check out [Awesome Sanic](https://github.com/mekicha/awesome-sanic).

Sanic uses [httpx](https://www.python-httpx.org/) inside of its testing package (sanic-testing) 😉.
```

***

## 完全に注釈を付けられたハンドラです

型アノテーションを使用している人のために...

```python
from sanic.response import HTTPResponse, text
from sanic.request import Request

@app.get("/typed")
async def typed_handler(request: Request) -> HTTPResponse:
    return text("Done")
```

## ハンドラーに名前を付けています

すべてのハンドラは自動的に名前が付けられます。 これは、デバッグやテンプレート内の URL を生成する際に便利です。 指定しない場合、使用される名前は関数の名前です。

.. 列::

```
例えば、このハンドラは `foo_handler` という名前になります。
```

.. 列::

````
```python
# Handler name will be "foo_handler"
@app.get("/foo")
async def foo_handler(request):
    return text("I said foo!")
```
````

.. 列::

```
しかし、デコレータに `name` 引数を渡すことで上書きできます。
```

.. 列::

````
```python
# Handler name will be "foo"
@app.get("/foo", name="foo")
async def foo_handler(request):
    return text("I said foo!")
```
````

.. 列::

```
実際には、**注意** が名前を与えなければならないことがあります。 例えば、同じ関数に 2 つのデコレータを使用する場合、少なくとも 1 つの名前を指定する必要があります。

しないとエラーが発生し、アプリが起動しません。名前は **必ず**一意でなければなりません。
```

.. 列::

````
```python
# Two handlers, same function,
# different names:
# - "foo_arg"
# - "foo"
@app.get("/foo/<arg>", name="foo_arg")
@app.get("/foo")
async def foo(request, arg=None):
    return text("I said foo!")
```
````
