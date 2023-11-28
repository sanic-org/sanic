# Background logger

The background logger requires both `sanic>=22.9` and `sanic-ext>=22.9`.

You can setup Sanic Extensions to log all of your messages from a background process. This requires that you not be in [single process mode](../../guide/deployment/manager.md#single-process-mode).

Logging can sometimes be an expensive operation. By pushing all logging off to a background process, you can potentially gain some performance benefits.

## Setup

.. column::

    Out of the box, the background logger is disabled. You will need to opt-in if you would like to use it.

.. column::

    ```python
    app.config.LOGGING = True
    ```

## How does it work

When enabled, the extension will create a `multoprocessing.Queue`. It will remove all handlers on the [default Sanic loggers](../../guide/best-practices/logging.md) and replace them with a [`QueueHandler`](https://docs.python.org/3/library/logging.handlers.html#queuehandler). When a message is logged, it will be pushed into the queue by the handler, and read by the background process to the log handlers that were originally in place. This means you can still configure logging as normal and it should "just work."

## Configuration

| Key | Type | Default| Description |
|--|--|--|--|
| LOGGING | `bool` | `False` | Whether to enable this extension. |
| LOGGING_QUEUE_MAX_SIZE | `int` | `4096` | The max size of the queue before messages are rejected. |
