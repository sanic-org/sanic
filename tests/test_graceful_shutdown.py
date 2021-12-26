import asyncio
import logging
import time

from multiprocessing import Process

import httpx


PORT = 42101


def test_no_exceptions_when_cancel_pending_request(app, caplog):
    app.config.GRACEFUL_SHUTDOWN_TIMEOUT = 1

    @app.get("/")
    async def handler(request):
        await asyncio.sleep(5)

    @app.after_server_start
    def shutdown(app, _):
        time.sleep(0.2)
        app.stop()

    def ping():
        time.sleep(0.1)
        response = httpx.get("http://127.0.0.1:8000")
        print(response.status_code)

    p = Process(target=ping)
    p.start()

    with caplog.at_level(logging.INFO):
        app.run()

    p.kill()

    info = 0
    for record in caplog.record_tuples:
        assert record[1] != logging.ERROR
        if record[1] == logging.INFO:
            info += 1
        if record[2].startswith("Request:"):
            assert record[2] == (
                "Request: GET http://127.0.0.1:8000/ stopped. "
                "Transport is closed."
            )
    assert info == 11
