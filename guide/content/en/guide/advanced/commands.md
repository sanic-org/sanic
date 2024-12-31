# Custom CLI Commands

.. new:: New in v24.12

    This feature was added in version 24.12

Sanic ships with a [CLI](../running/running.html#running-via-command) for running the Sanic server. Sometimes, you may have the need to enhance that CLI to run your own custom commands. Commands are invoked using the following basic pattern:

```sh
sanic path.to:app exec <command> [--arg=value]
```

.. column::

    To enable this, you can use your `Sanic` app instance to wrap functions that can be callable from the CLI using the `@app.command` decorator.

.. column::

    ```python
    @app.command
    async def hello(name="world"):
        print(f"Hello, {name}.")
    ```
    
.. column::

    Now, you can easily invoke this command using the `exec` action. 
    
.. column::

    ```sh
    sanic path.to:app exec hello --name=Adam
    ```
    
Command handlers can be either synchronous or asynchronous. The handler can accept any number of keyword arguments, which will be passed in from the CLI.

.. column::

    By default, the name of the function will be the command name. You can override this by passing the `name` argument to the decorator.
    
.. column::

    ```python
    @app.command(name="greet")
    async def hello(name="world"):
        print(f"Hello, {name}.")
    ```
    
    ```sh
    sanic path.to:app exec greet --name=Adam
    ```

.. warning::

    This feature is still in **BETA** and may change in future versions. There is no type coercion or validation on the arguments passed in from the CLI, and the CLI will ignore any return values from the command handler. Future enhancements and changes are likely.

*Added in v24.12*
