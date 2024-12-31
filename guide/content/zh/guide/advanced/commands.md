# 自定义 CLI 命令

.. 新：v24.12

```
This feature was added in version 24.12
```

使用 [CLI]的Sanic 飞船(../running/running.html#running-via-command) 运行Sanic 服务器。 有时，您可能需要提高CLI来运行您自己的自定义命令。 命令使用以下基本模式：

```sh
sanic path.to:app exec <command> [--arg=value]
```

.. 列:

```
To enable this, you can use your `Sanic` app instance to wrap functions that can be callable from the CLI using the `@app.command` decorator.
```

.. 列:

````
```python
@app.command
async def hello(name="world"):
    print(f"Hello, {name}.")
```
````

.. 列:

```
Now, you can easily invoke this command using the `exec` action. 
```

.. 列:

````
```sh
sanic path.to:app exec hello --name=Adam
```
````

命令处理程序可以是同步或异步的。 处理程序可以接受任何一些关键词参数，这些参数将从CLI传递。

.. 列:

```
By default, the name of the function will be the command name. You can override this by passing the `name` argument to the decorator.
```

.. 列:

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

.. 警告：:

```
This feature is still in **BETA** and may change in future versions. There is no type coercion or validation on the arguments passed in from the CLI, and the CLI will ignore any return values from the command handler. Future enhancements and changes are likely.
```

_添加于 v24.12_
