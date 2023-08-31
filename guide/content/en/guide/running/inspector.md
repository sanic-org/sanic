# Inspector

The Sanic Inspector is a feature of Sanic Server. It is *only* available when running Sanic with the built-in [worker manager](./manager.md).

It is an HTTP application that *optionally* runs in the background of your application to allow you to interact with the running instance of your application.


.. tip:: INFO

    The Inspector was introduced in limited capacity in v22.9, but the documentation on this page assumes you are using v22.12 or higher.


## Getting Started

The inspector is disabled by default. To enable it, you have two options.

.. column::

    Set a flag when creating your application instance.

.. column::

    ```python
    app = Sanic("TestApp", inspector=True)
    ```


.. column::

    Or, set a configuration value.

.. column::

    ```python
    app = Sanic("TestApp")
    app.config.INSPECTOR = True
    ```



.. warning:: 

    If you are using the configuration value, it *must* be done early and before the main worker process starts. This means that it should either be an environment variable, or it should be set shortly after creating the application instance as shown above.



## Using the Inspector

Once the inspector is running, you will have access to it via the CLI or by directly accessing its web API via HTTP.

.. column::

    **Via CLI**
    ```sh
    sanic inspect
    ```

.. column::

    **Via HTTP**
    ```sh
    curl http://localhost:6457
    ```



.. note:: 

    Remember, the Inspector is not running on your Sanic application. It is a seperate process, with a seperate application, and exposed on a seperate socket.



## Built-in Commands

The Inspector comes with the following built-in commands. 

| CLI Command        | HTTP Action                        | Description                                                              |
|--------------------|------------------------------------|--------------------------------------------------------------------------|
| `inspect`          | `GET /`                            | Display basic details about the running application.                     |
| `inspect reload`   | `POST /reload`                     | Trigger a reload of all server workers.                                  |
| `inspect shutdown` | `POST /shutdown`                   | Trigger a shutdown of all processes.                                     |
| `inspect scale N`  | `POST /scale`<br>`{"replicas": N}` | Scale the number of workers. Where `N` is the target number of replicas. |

## Custom Commands

The Inspector is easily extendable to add custom commands (and endpoints).

.. column::

    Subclass the `Inspector` class and create arbitrary methods. As long as the method name is not preceded by an underscore (`_`), then the name of the method will be a new subcommand on the inspector.

.. column::

    ```python
    from sanic import json
    from sanic.worker.inspector import Inspector

    class MyInspector(Inspector):
        async def something(self, *args, **kwargs):
            print(args)
            print(kwargs)

    app = Sanic("TestApp", inspector_class=MyInspector, inspector=True)
    ```

This will expose custom methods in the general pattern:

- CLI: `sanic inspect <method_name>`
- HTTP: `POST /<method_name>`

It is important to note that the arguments that the new method accepts are derived from how you intend to use the command. For example, the above `something` method accepts all positional and keyword based parameters.

.. column::

    In the CLI, the positional and keyword parameters are passed as either positional or keyword arguments to your method. All values will be a `str` with the following exceptions:

    - A keyword parameter with no assigned value will be: `True`
    - Unless the parameter is prefixed with `no-`, then it will be: `False`

.. column::

    ```sh
    sanic inspect something one two three --four --no-five --six=6
    ```
    In your application log console, you will see:
    ```
    ('one', 'two', 'three')
    {'four': True, 'five': False, 'six': '6'}
    ```


.. column::

    The same can be achieved by hitting the API directly. You can pass arguments to the method by exposing them in a JSON payload. The only thing to note is that the positional arguments should be exposed as `{"args": [...]}`.

.. column::

    ```sh
    curl http://localhost:6457/something \
      --json '{"args":["one", "two", "three"], "four":true, "five":false, "six":6}'
    ```
    In your application log console, you will see:
    ```
    ('one', 'two', 'three')
    {'four': True, 'five': False, 'six': 6}
    ```


## Using in production


.. danger:: 

    Before exposing the Inspector on a product, please consider all of the options in this section carefully.


When running Inspector on a remote production instance, you can protect the endpoints by requiring TLS encryption, and requiring API key authentication.

### TLS encryption

.. column::

    To the Inspector HTTP instance over TLS, pass the paths to your certificate and key.

.. column::

    ```python
    app.config.INSPECTOR_TLS_CERT = "/path/to/cert.pem"
    app.config.INSPECTOR_TLS_KEY = "/path/to/key.pem"
    ```


.. column::

    This will require use of the `--secure` flag, or `https://`.

.. column::

    ```sh
    sanic inspect --secure --host=<somewhere>
    ```
    ```sh
    curl https://<somewhere>:6457
    ```

### API Key Authentication

.. column::

    You can secure the API with bearer token authentication.

.. column::

    ```python
    app.config.INSPECTOR_API_KEY = "Super-Secret-200"
    ```


.. column::

    This will require the `--api-key` parameter, or bearer token authorization header.

.. column::

    ```sh
    sanic inspect --api-key=Super-Secret-200
    ```
    ```sh
    curl http://localhost:6457  -H "Authorization: Bearer Super-Secret-200"
    ```

## Configuration

See [configuration](./configuration.md)
