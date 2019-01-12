import asyncio
import os

from functools import partial
from inspect import isawaitable
from multiprocessing import Process
from signal import SIG_IGN, SIGINT, SIGTERM, Signals
from signal import signal as signal_func
from socket import SO_REUSEADDR, SOL_SOCKET, socket
from time import time

from sanic.log import logger
from sanic.protocol import HttpProtocol


try:
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass


current_time = None


class Signal:
    stopped = False


def update_current_time(loop):
    """Cache the current time, since it is needed at the end of every
    keep-alive request to update the request timeout time

    :param loop:
    :return:
    """
    global current_time
    current_time = time()
    loop.call_later(1, partial(update_current_time, loop))


def trigger_events(events, loop):
    """Trigger event callbacks (functions or async)

    :param events: one or more sync or async functions to execute
    :param loop: event loop
    """
    for event in events:
        result = event(loop)
        if isawaitable(result):
            loop.run_until_complete(result)


def create_server(
    host,
    port,
    request_handler,
    error_handler,
    before_start=None,
    after_start=None,
    before_stop=None,
    after_stop=None,
    debug=False,
    request_timeout=60,
    response_timeout=60,
    keep_alive_timeout=5,
    ssl=None,
    sock=None,
    request_max_size=None,
    request_buffer_queue_size=100,
    reuse_port=False,
    loop=None,
    protocol=HttpProtocol,
    backlog=100,
    register_sys_signals=True,
    run_multiple=False,
    run_async=False,
    connections=None,
    signal=Signal(),
    request_class=None,
    access_log=True,
    keep_alive=True,
    is_request_stream=False,
    router=None,
    websocket_max_size=None,
    websocket_max_queue=None,
    websocket_read_limit=2 ** 16,
    websocket_write_limit=2 ** 16,
    state=None,
    server_kwargs=None,
):
    if not run_async:
        # create new event_loop after fork
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if debug:
        loop.set_debug(debug)

    connections = connections if connections is not None else set()
    server = partial(
        protocol,
        loop=loop,
        connections=connections,
        signal=signal,
        request_handler=request_handler,
        error_handler=error_handler,
        request_timeout=request_timeout,
        response_timeout=response_timeout,
        keep_alive_timeout=keep_alive_timeout,
        request_max_size=request_max_size,
        request_class=request_class,
        access_log=access_log,
        keep_alive=keep_alive,
        is_request_stream=is_request_stream,
        router=router,
        websocket_max_size=websocket_max_size,
        websocket_max_queue=websocket_max_queue,
        websocket_read_limit=websocket_read_limit,
        websocket_write_limit=websocket_write_limit,
        state=state,
        debug=debug,
    )
    server_kwargs = server_kwargs if server_kwargs else {}
    server_coroutine = loop.create_server(
        server,
        host,
        port,
        ssl=ssl,
        reuse_port=reuse_port,
        sock=sock,
        backlog=backlog,
        **server_kwargs
    )

    # Instead of pulling time at the end of every request,
    # pull it once per minute
    loop.call_soon(partial(update_current_time, loop))

    if run_async:
        return server_coroutine

    trigger_events(before_start, loop)

    try:
        http_server = loop.run_until_complete(server_coroutine)
    except BaseException:
        logger.exception("Unable to start server")
        return

    trigger_events(after_start, loop)

    # Ignore SIGINT when run_multiple
    if run_multiple:
        signal_func(SIGINT, SIG_IGN)

    # Register signals for graceful termination
    if register_sys_signals:
        _singals = (SIGTERM,) if run_multiple else (SIGINT, SIGTERM)
        for _signal in _singals:
            try:
                loop.add_signal_handler(_signal, loop.stop)
            except NotImplementedError:
                logger.warning(
                    "Sanic tried to use loop.add_signal_handler "
                    "but it is not implemented on this platform."
                )

    return http_server


def serve(
    host,
    port,
    request_handler,
    error_handler,
    before_start=None,
    after_start=None,
    before_stop=None,
    after_stop=None,
    debug=False,
    request_timeout=60,
    response_timeout=60,
    keep_alive_timeout=5,
    ssl=None,
    sock=None,
    request_max_size=None,
    request_buffer_queue_size=100,
    reuse_port=False,
    loop=None,
    protocol=HttpProtocol,
    backlog=100,
    register_sys_signals=True,
    run_multiple=False,
    run_async=False,
    connections=None,
    signal=Signal(),
    request_class=None,
    access_log=True,
    keep_alive=True,
    is_request_stream=False,
    router=None,
    websocket_max_size=None,
    websocket_max_queue=None,
    websocket_read_limit=2 ** 16,
    websocket_write_limit=2 ** 16,
    state=None,
    graceful_shutdown_timeout=15.0,
):
    """Start asynchronous HTTP Server on an individual process.

    :param host: Address to host on
    :param port: Port to host on
    :param request_handler: Sanic request handler with middleware
    :param error_handler: Sanic error handler with middleware
    :param before_start: function to be executed before the server starts
                         listening. Takes arguments `app` instance and `loop`
    :param after_start: function to be executed after the server starts
                        listening. Takes  arguments `app` instance and `loop`
    :param before_stop: function to be executed when a stop signal is
                        received before it is respected. Takes arguments
                        `app` instance and `loop`
    :param after_stop: function to be executed when a stop signal is
                       received after it is respected. Takes arguments
                       `app` instance and `loop`
    :param debug: enables debug output (slows server)
    :param request_timeout: time in seconds
    :param response_timeout: time in seconds
    :param keep_alive_timeout: time in seconds
    :param ssl: SSLContext
    :param sock: Socket for the server to accept connections from
    :param request_max_size: size in bytes, `None` for no limit
    :param reuse_port: `True` for multiple workers
    :param loop: asyncio compatible event loop
    :param protocol: subclass of asyncio protocol class
    :param request_class: Request class to use
    :param access_log: disable/enable access log
    :param websocket_max_size: enforces the maximum size for
                               incoming messages in bytes.
    :param websocket_max_queue: sets the maximum length of the queue
                                that holds incoming messages.
    :param websocket_read_limit: sets the high-water limit of the buffer for
                                 incoming bytes, the low-water limit is half
                                 the high-water limit.
    :param websocket_write_limit: sets the high-water limit of the buffer for
                                  outgoing bytes, the low-water limit is a
                                  quarter of the high-water limit.
    :param is_request_stream: disable/enable Request.stream
    :param request_buffer_queue_size: streaming request buffer queue size
    :param router: Router object
    :param graceful_shutdown_timeout: How long take to Force close non-idle
                                      connection
    :return: Nothing
    """
    if not run_async:
        # create new event_loop after fork
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if debug:
        loop.set_debug(debug)

    connections = connections if connections is not None else set()
    server = partial(
        protocol,
        loop=loop,
        connections=connections,
        signal=signal,
        request_handler=request_handler,
        error_handler=error_handler,
        request_timeout=request_timeout,
        response_timeout=response_timeout,
        keep_alive_timeout=keep_alive_timeout,
        request_max_size=request_max_size,
        request_class=request_class,
        access_log=access_log,
        keep_alive=keep_alive,
        is_request_stream=is_request_stream,
        router=router,
        websocket_max_size=websocket_max_size,
        websocket_max_queue=websocket_max_queue,
        websocket_read_limit=websocket_read_limit,
        websocket_write_limit=websocket_write_limit,
        state=state,
        debug=debug,
    )

    server_coroutine = loop.create_server(
        server,
        host,
        port,
        ssl=ssl,
        reuse_port=reuse_port,
        sock=sock,
        backlog=backlog,
    )

    # Instead of pulling time at the end of every request,
    # pull it once per minute
    loop.call_soon(partial(update_current_time, loop))

    if run_async:
        return server_coroutine

    trigger_events(before_start, loop)

    try:
        http_server = loop.run_until_complete(server_coroutine)
    except BaseException:
        logger.exception("Unable to start server")
        return

    trigger_events(after_start, loop)

    # Ignore SIGINT when run_multiple
    if run_multiple:
        signal_func(SIGINT, SIG_IGN)

    # Register signals for graceful termination
    if register_sys_signals:
        _singals = (SIGTERM,) if run_multiple else (SIGINT, SIGTERM)
        for _signal in _singals:
            try:
                loop.add_signal_handler(_signal, loop.stop)
            except NotImplementedError:
                logger.warning(
                    "Sanic tried to use loop.add_signal_handler "
                    "but it is not implemented on this platform."
                )
    pid = os.getpid()
    try:
        logger.info("Starting worker [%s]", pid)
        loop.run_forever()
    finally:
        logger.info("Stopping worker [%s]", pid)

        stop_server(
            http_server,
            connections=connections,
            signal=signal,
            before_stop=before_stop,
            after_stop=after_stop,
            graceful_shutdown_timeout=graceful_shutdown_timeout,
        )


def stop_server(http_server, connections=None, signal=Signal(),
                before_stop=None, after_stop=None,
                loop=None, graceful_shutdown_timeout=15.0):
    trigger_events(before_stop, loop)

    # Wait for event loop to finish and all connections to drain
    http_server.close()
    loop.run_until_complete(http_server.wait_closed())

    # Complete all tasks on the loop
    signal.stopped = True
    for connection in connections:
        connection.close_if_idle()

    # Gracefully shutdown timeout.
    # We should provide graceful_shutdown_timeout,
    # instead of letting connection hangs forever.
    # Let's roughly calcucate time.
    start_shutdown = 0
    while connections and (start_shutdown < graceful_shutdown_timeout):
        loop.run_until_complete(asyncio.sleep(0.1))
        start_shutdown = start_shutdown + 0.1

    # Force close non-idle connection after waiting for
    # graceful_shutdown_timeout
    coros = []
    for conn in connections:
        if hasattr(conn, "websocket") and conn.websocket:
            coros.append(conn.websocket.close_connection())
        else:
            conn.close()

    _shutdown = asyncio.gather(*coros, loop=loop)
    loop.run_until_complete(_shutdown)

    trigger_events(after_stop, loop)

    loop.close()


def serve_multiple(server_settings, workers):
    """Start multiple server processes simultaneously.  Stop on interrupt
    and terminate signals, and drain connections when complete.

    :param server_settings: kw arguments to be passed to the serve function
    :param workers: number of workers to launch
    :param stop_event: if provided, is used as a stop signal
    :return:
    """
    server_settings["reuse_port"] = True
    server_settings["run_multiple"] = True

    # Handling when custom socket is not provided.
    if server_settings.get("sock") is None:
        sock = socket()
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.bind((server_settings["host"], server_settings["port"]))
        sock.set_inheritable(True)
        server_settings["sock"] = sock
        server_settings["host"] = None
        server_settings["port"] = None

    def sig_handler(signal, frame):
        logger.info("Received signal %s. Shutting down.", Signals(signal).name)
        for process in processes:
            os.kill(process.pid, SIGTERM)

    signal_func(SIGINT, lambda s, f: sig_handler(s, f))
    signal_func(SIGTERM, lambda s, f: sig_handler(s, f))

    processes = []

    for _ in range(workers):
        process = Process(target=serve, kwargs=server_settings)
        process.daemon = True
        process.start()
        processes.append(process)

    for process in processes:
        process.join()

    # the above processes will block this until they're stopped
    for process in processes:
        process.terminate()
    server_settings.get("sock").close()
