# リスナー

Sanicは、アプリケーションサーバーのライフサイクルにオペレーションを注入する8つの(8)機会を提供します。 これには [signals](../advanced/signals.md) は含まれません。

メインの Sanic プロセスで **のみ** を実行する (2) が2つあります (例: `sanic server.app` を呼び出すごとに1回です)。

- `main_process_start`
- `main_process_stop`

自動リロードがオンになっている場合、リローダープロセスで **のみ** 動作する (2) もあります。

- `reload_process_start`
- `reload_process_stop`

_v22.3_ に `reload_process_start` と `reload_process_stop` を追加しました

サーバーが起動または終了すると、起動/分解コードを実行することができる4つの(4)があります。

- `before_server_start`
- `after_server_start`
- `before_server_stop`
- `after_server_stop`

ワーカープロセスのライフサイクルは次のようになります。

.. mermaid::

```
sequenceDiagram
autonumber
participant Process
participant Worker
participant Listener
participant Handler
Note over Process: sanic server.app
loop
    Process->>Listener: @app.main_process_start
    Listener->>Handler: Invoke event handler
end
Process->>Worker: Run workers
loop Start each worker
    loop
        Worker->>Listener: @app.before_server_start
        Listener->>Handler: Invoke event handler
    end
    Note over Worker: Server status: started
    loop
        Worker->>Listener: @app.after_server_start
        Listener->>Handler: Invoke event handler
    end
    Note over Worker: Server status: ready
end
Process->>Worker: Graceful shutdown
loop Stop each worker
    loop
        Worker->>Listener: @app.before_server_stop
        Listener->>Handler: Invoke event handler
    end
    Note over Worker: Server status: stopped
    loop
        Worker->>Listener: @app.after_server_stop
        Listener->>Handler: Invoke event handler
    end
    Note over Worker: Server status: closed
end
loop
    Process->>Listener: @app.main_process_stop
    Listener->>Handler: Invoke event handler
end
Note over Process: exit
```

Sanicプロセスの開始と停止を担当するプロセスの中で、このワーカープロセスの外で再ローダープロセスが稼働しています。 次の例を考えてみましょう:

```python
@app.reload_process_start
async def reload_start(*_):
    print(">>>>>> reload_start <<<<<<")

@app.main_process_start
async def main_start(*_):
    print(">>>>>> main_start <<<<<<")
	
@app.before_server_start
async def before_start(*_):
	print(">>>>>> before_start <<<<<<")
```

このアプリケーションが自動再読み込みをオンにして実行された場合、`reload_start` 関数は、リローダーのプロセスが開始されたときに呼び出されます。 メインプロセスが開始されると、 `main_start` 関数も呼び出されます。 **HOWEVER**、`before_start` 関数は、開始されるワーカープロセスごとに1回呼び出されます。 その後、ファイルが保存されワーカーが再起動されるたびに実行されます。

## リスナーをアタッチする

.. 列::

```
リスナーとして関数をセットアップするプロセスは、route (ルート)を宣言するプロセスと似ています。

現在実行されている `Sanic()` インスタンスはリスナーに挿入されます。
```

.. 列::

````
```python
async def setup_db(app):
    app.ctx.db = await db_setup()

app.register_listener(setup_db, "before_server_start")
```
````

.. 列::

```
`Sanic`アプリインスタンスには、利便性のデコレータもあります。
```

.. 列::

````
```python
@app.listener("before_server_start")
async def setup_db(app):
    app.ctx.db = await db_setup()
```
````

.. 列::

```
v22.3 より前には、アプリケーションインスタンスとカレントイベントループの両方が関数に注入されました。 ただし、デフォルトではアプリケーションインスタンスのみが注入されます。 関数署名が両方を受け入れる場合は、ここで示すようにアプリケーションとループの両方が注入されます。
```

.. 列::

````
```python
@app.listener("before_server_start")
async def setup_db(app, loop):
    app.ctx.db = await db_setup()
```
````

.. 列::

```
デコレータをさらに短くすることができます。オートコンプリート付きの IDE がある場合に便利です。
```

.. 列::

````
```python
@app.before_server_start
async def setup_db(app):
    app.ctx.db = await db_setup()
```
````

## 実行の順序

リスナーは起動時に宣言された順に実行され、分解中に宣言された順に逆順になります。

|                       | 段階      | ご注文           |
| --------------------- | ------- | ------------- |
| `main_process_start`  | メインの起動  | regular 🙂 ⬇️ |
| `before_server_start` | ワーカーの起動 | regular 🙂 ⬇️ |
| `after_server_start`  | ワーカーの起動 | regular 🙂 ⬇️ |
| `before_server_stop`  | ワーカーの停止 | 🙃 ⬆️         |
| `after_server_stop`   | ワーカーの停止 | 🙃 ⬆️         |
| `main_process_stop`   | メインシャット | 🙃 ⬆️         |

次の設定を考えると、2つのworker を実行した場合、コンソールでこれを確認する必要があります。

.. 列::

````
```python
@app.listener("before_server_start")
async def listener_1(app, loop):
    print("listener_1")

@app.before_server_start
async def listener_2(app, loop):
    print("listener_2")

@app.listener("after_server_start")
async def listener_3(app, loop):
    print("listener_3")

@app.after_server_start
async def listener_4(app, loop):
    print("listener_4")

@app.listener("before_server_stop")
async def listener_5(app, loop):
    print("listener_5")

@app.before_server_stop
async def listener_6(app, loop):
    print("listener_6")

@app.listener("after_server_stop")
async def listener_7(app, loop):
    print("listener_7")

@app.after_server_stop
async def listener_8(app, loop):
    print("listener_8")
```
````

.. 列::

````
```bash
[pid: 1000000] [INFO] Goin' Fast @ http://127.0.0.1:9999
[pid: 1000000] [INFO] listener_0
[pid: 1111111] [INFO] listener_1
[pid: 1111111] [INFO] listener_2
[pid: 1111111] [INFO] listener_3
[pid: 1111111] [INFO] listener_4
[pid: 1111111] [INFO] Starting worker [1111111]
[pid: 1222222] [INFO] listener_1
[pid: 1222222] [INFO] listener_2
[pid: 1222222] [INFO] listener_3
[pid: 1222222] [INFO] listener_4
[pid: 1222222] [INFO] Starting worker [1222222]
[pid: 1111111] [INFO] Stopping worker [1111111]
[pid: 1222222] [INFO] Stopping worker [1222222]
[pid: 1222222] [INFO] listener_6
[pid: 1222222] [INFO] listener_5
[pid: 1222222] [INFO] listener_8
[pid: 1222222] [INFO] listener_7
[pid: 1111111] [INFO] listener_6
[pid: 1111111] [INFO] listener_5
[pid: 1111111] [INFO] listener_8
[pid: 1111111] [INFO] listener_7
[pid: 1000000] [INFO] listener_9
[pid: 1000000] [INFO] Server Stopped
```
In the above example, notice how there are three processes running:

- `pid: 1000000` - The *main* process
- `pid: 1111111` - Worker 1
- `pid: 1222222` - Worker 2

*Just because our example groups all of one worker and then all of another, in reality since these are running on separate processes, the ordering between processes is not guaranteed. But, you can be sure that a single worker will **always** maintain its order.*
````

.. tip:: FYI

```
実際の結果は、 `before_server_start` ハンドラの最初のリスナーがデータベース接続を設定する場合です。 その後登録されたリスナーはその接続が生きていることに頼ることができます 開始時と停止時の両方。
```

### 優先度

v23.12 では `priority` キーワード引数がリスナーに追加されました。 これにより、リスナーの実行順序を微調整できます。 デフォルトの優先度は `0` です。 優先度が高いリスナーが最初に実行されます。 同じ優先度を持つリスナーは、登録された順に実行されます。 さらに、 `app` インスタンスにアタッチされたリスナーは、 `Blueprint` インスタンスにアタッチされたリスナーの前に実行されます。

全体的に実行の順序を決定するためのルールは次のとおりです。

1. 降順の優先度
2. Blueprint リスナーより前のアプリのリスナー
3. 登録注文

.. 列::

````
一例として、以下のようなものを考えてみましょう。 これは

```bash
third
bp_third
second
bp_second
first
fth
bp_first
```
````

.. 列::

````
```python
@app.before_server_start
async def first(app):
    print("first")

@app.listener("before_server_start", priority=2)
async def second(app):
    print("second")

@app.before_server_start(priority=3)
async def third(app):
    print("third")

@bp.before_server_start
async def bp_first(app):
    print("bp_first")

@bp.listener("before_server_start", priority=2)
async def bp_second(app):
    print("bp_second")

@bp.before_server_start(priority=3)
async def bp_third(app):
    print("bp_third")

@app.before_server_start
async def fourth(app):
    print("fourth")

app.blueprint(bp)
```
````

## ASGI モード

ASGI サーバーでアプリケーションを実行している場合は、次の変更を確認してください。

- `reload_process_start` と `reload_process_stop` は **無視されます**
- `main_process_start` と `main_process_stop` は **無視されます**
- `before_server_start` はできるだけ早く実行され、`after_server_start` の前に実行されますが、技術的にはその時点で既に実行されています
- `after_server_stop` はできるだけ遅く実行され、`before_server_stop` の後になりますが、技術的には、サーバーはその時点で動作しています。
