# カスタムCLIコマンド

.. new:: v24.12 の新機能

```
This feature was added in version 24.12
```

Sanic は Sanic サーバを実行するための [CLI](../running/running.html#running-via-command) を搭載しています。 場合によっては、独自のコマンドを実行するためにCLIを強化する必要があるかもしれません。 コマンドは以下の基本パターンを使用して呼び出されます。

```sh
sanic path.to:app exec <command> [--arg=value]
```

.. 列::

```
To enable this, you can use your `Sanic` app instance to wrap functions that can be callable from the CLI using the `@app.command` decorator.
```

.. 列::

````
```python
@app.command
async def hello(name="world"):
    print(f"Hello, {name}.")
```
````

.. 列::

```
Now, you can easily invoke this command using the `exec` action. 
```

.. 列::

````
```sh
sanic path.to:app exec hello --name=Adam
```
````

コマンドハンドラは同期または非同期のどちらでも構いません。 ハンドラは、CLI から渡される任意の数のキーワード引数を受け入れることができます。

.. 列::

```
By default, the name of the function will be the command name. You can override this by passing the `name` argument to the decorator.
```

.. 列::

````
```python
@app.command(name="greet")
async def hello(name="world"):
    print(f"Hello, {name}.")
```

```sh
sanic path.to:app exec greet --name=Adam
```
````

.. 警告::

```
This feature is still in **BETA** and may change in future versions. There is no type coercion or validation on the arguments passed in from the CLI, and the CLI will ignore any return values from the command handler. Future enhancements and changes are likely.
```

_V24.12_に追加しました
