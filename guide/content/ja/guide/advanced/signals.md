# シグナル

シグナルは、アプリケーションのある部分が別の部分に何かが起こったことを伝える方法を提供します。

```python
@app.signal("user.registration.created")
async def send_registration_email(**context):
    await send_email(context["email"], template="registration")

@app.post("/register")
async def handle_registration(request):
    await do_registration(request)
    await request.app.dispatch(
        "user.registration.created",
        context={"email": request.json.email}
    })
```

## シグナルを追加する

.. column::

```
シグナルを追加するためのAPIは、ルートの追加と非常によく似ています。
```

.. column::

````
```python
async def my_signal_handler():
    print("何かが起こった")

app.add_signal(my_signal_handler, "something.happed.ohmy")
```
````

.. 列::

```
しかし、おそらくもう少し便利な方法は、組み込みのデコレータを使用することです。
```

.. 列::

````
```python
@app.signal("something.happened.ohmy")
async def my_signal_handler():
    print("something")
```
````

.. 列::

```
シグナルに条件(conditions)が必要な場合は、ハンドラを追加する際に必ず追加してください。
```

.. 列::

````
```python
async def my_signal_handler1():
    print("何かが起こった")

app.add_signal(
    my_signal_handler,
    "something.happened.ohmy1",
    conditions={"some_condition": "value"}
)

@app.signal("something.happened.ohmy2", conditions={"some_condition": "value"})
async def my_signal_handler2():
    print("何かが起こった")
```
````

.. 列::

```
シグナルはblueprintsで宣言することもできます。
```

.. 列::

````
```python
bp = Blueprint("foo")

@bp.signal("something.happened.ohmy")
async def my_signal_handler():
    print("何かが起こった")
```
````

## ビルトインシグナル

新しいシグナルを作成することに加えて、Sanic自体からディスパッチされる組み込みシグナルがいくつかあります。 これらのシグナルは、開発者に要求とサーバーのライフサイクルに機能を追加する機会を増やすために存在します。

_v21.9で追加_

.. column::

```
他のシグナルと同じように、アプリケーションまたはブループリントインスタンスにアタッチできます。
```

.. column::

````
```python
@app.signal("http.lifycle.complete")
async def my_signal_handler(conn_info):
    print("Connection has been closed")
```
````

これらのシグナルは、ハンドラが取る引数、およびアタッチする条件(存在する場合)とともに、利用可能なシグナルです。

| イベント名                     | 引数                              | 条件                                                         |
| ------------------------- | ------------------------------- | ---------------------------------------------------------- |
| `http.routing.before`     | request                         |                                                            |
| `http.routing.after`      | request, route, kwargs, handler |                                                            |
| `http.handler.before`     | request                         |                                                            |
| `http.handler.after`      | request                         |                                                            |
| `http.lifycle.begin`      | conn_info  |                                                            |
| `http.lifycle.read_head`  | head                            |                                                            |
| `http.lifycle.request`    | request                         |                                                            |
| `http.lifycle.handle`     | request                         |                                                            |
| `http.lifycle.read_body`  | body                            |                                                            |
| `http.lifycle.exception`  | request, exception              |                                                            |
| `http.lifycle.response`   | request, response               |                                                            |
| `http.lifycle.send`       | data                            |                                                            |
| `http.lifycle.complete`   | conn_info  |                                                            |
| `http.middleware.before`  | request, response               | `{"attach_to": "request"}` または `{"attach_to": "response"}` |
| `http.middleware.after`   | request, response               | `{"attach_to": "request"}` または `{"attach_to": "response"}` |
| `server.exception.report` | app, exception                  |                                                            |
| `server.init.before`      | app, loop                       |                                                            |
| `server.init.after`       | app, loop                       |                                                            |
| `server.shutdown.before`  | app, loop                       |                                                            |
| `server.shutdown.after`   | app, loop                       |                                                            |

バージョン22.9で`http.handler.before`と`http.handler.after`が追加されました。

バージョン23.6で`server.exception.report`が追加されました。

.. column::

```
ビルトインシグナルを使いやすくするために、許可されたビルトインをすべて含む `Enum` オブジェクトが用意されています。 最近の IDE では、イベント名の完全なリストを文字列として覚えておく必要がないので、これは便利です。

*v21.12で追加*
```

.. column::

````
```python
from sanic.signal import Event

@app.signal(Event.HTTP_LIFECYCLE_COMPLETE)
async def my_signal_handler(conn_info):
    print("Connection has been closed")
```
````

## イベント

.. column::

```
シグナルは _event_ に基づいています。イベントは以下のパターンの単なる文字列です。
```

.. column::

````
```
namespace.reference.action
```
````

.. tip:: イベントには3つの部分が必要です。 何を使っていいかわからない場合は、次のパターンを試してみてください。

```
- `my_app.something.happened`
- `sanic.notice.hello`
```

### イベントパラメータ

.. column::

```
イベントは「動的」であり、[pathパラメータ](../basics/routing.md#path-parameters)と同じ構文を使用して宣言できます。これにより、任意の値に基づいてマッチングできます。
```

.. 列::

````
```python
@app.signal("foo.bar.<thing>")
async def signal_handler(thing):
    print(f"[signal_handler] {thing=}")

@app.get("/")
async def trigger(request):
    await app.dispatch("foo.bar.baz")
    return response.text("完了。")
```
````

利用可能な型定義に関する詳細は[pathパラメータ](../basics/routing.md#path-parameters)を参照してください。

.. info:: イベントの3番目の部分(アクション)のみが動的です。

```
- `foo.bar.<thing>` 🆗
- `foo.<bar>.baz` ❌
```

### 待つ

.. column::

```
アプリケーションは、シグナルハンドラを実行するだけでなく、イベントがトリガーされるのを待つこともできます。
```

.. column::

````
```python
await app.event("foo.bar.baz")
```
````

.. column::

```
**重要**: 待つことはブロッキング機能です。したがって、これを[バックグラウンドタスク](../basics/tasks.md)で実行する必要があります。
```

.. column::

````
```python
async def wait_for_event(app):
    while True:
        print("> 待機中")
        await app.event("foo.bar.baz")
        print("> イベント発見\n")

@app.after_server_start
async def after_server_start(app, loop):
    app.add_task(wait_for_event(app))
```
````

.. column::

```
イベントが動的パスで定義されている場合は、`*`を使用して任意のアクションをキャッチできます。
```

.. column::

````
```python
@app.signal("foo.bar.<thing>")

...

await app.event("foo.bar.*")
```
````

## ディスパッチ

_将来的には、Sanicは開発者がライフサイクルイベントに参加するのを支援するために、いくつかのイベントを自動的にディスパッチするようになります。_

.. column::

```
イベントをディスパッチすると、2つのことを行います。

1. イベントで定義されたシグナルハンドラを実行し、
2. イベントが完了するまで「待っている」ことをすべて解決します。
```

.. column::

````
```python
@app.signal("foo.bar.<thing>")
async def foo_bar(thing):
    print(f"{thing=}")

await app.dispatch("foo.bar.baz")
```
```
thing=baz
```
````

### コンテキスト

.. column::

```
シグナルハンドラに追加情報を渡す必要がある場合があります。 上記の最初の例では、ユーザーのメールアドレスを持つようにメール登録プロセスを望んでいました。
```

.. column::

````
```python
@app.signal("user.registration.created")
async def send_registration_email(**context):
    print(context)

await app.dispatch(
    "user.registration.created",
    context={"hello": "world"}
)
```
```
{'hello': 'world'}
```
````

.. tip:: 参考

```
シグナルはバックグラウンドタスクでディスパッチされます。
```

### Blueprints

Blueprintシグナルのディスパッチは、[ミドルウェア](../basics/middleware.md)と同様に機能します。 appレベルから行われるシグナルは、blueprintにも伝播します。 ただし、blueprintでディスパッチすると、そのblueprintで定義されているシグナルのみが実行されます。

.. column::

```
おそらく、例は説明しやすいでしょう:
```

.. column::

````
```python
bp = Blueprint("bp")

app_counter = 0
bp_counter = 0

@app.signal("foo.bar.baz")
def app_signal():
    nonlocal app_counter
    app_counter += 1

@bp.signal("foo.bar.baz")
def bp_signal():
    nonlocal bp_counter
    bp_counter += 1
```
````

.. column::

```
`app.dispatch("foo.bar.baz")`を実行すると、両方のシグナルが実行されます。
```

.. column::

````
```python
await app.dispatch("foo.bar.baz")
assert app_counter == 1
assertt bp_counter == 1
```
````

.. column::

```
`bp.dispatch("foo.bar.baz")`を実行すると、Blueprintシグナルのみが実行されます。
```

.. column::

````
```python
await bp.dispatch("foo.bar.baz")
assertt app_counter == 1
assertt bp_counter == 2
```
````
