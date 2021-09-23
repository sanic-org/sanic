import asyncio
import logging
from sanic import Sanic
from sanic.response import file
from sanic.log import error_logger
import time
error_logger.setLevel(logging.INFO)
app = Sanic(__name__)

@app.route('/')
async def index(request):
    return await file('websocket_bench.html')


@app.websocket('/bench')
async def bench_p_time(request, ws):
    i = 0
    bytes_total = 0
    start = 0
    end_time = 0
    started = False
    await ws.send("1")
    while started is False or (end_time > time.time()):
        i += 1
        in_data = await ws.recv()
        if started is False:
            del in_data
            error_logger.info("received first data: starting benchmark now..")
            started = True
            start = time.time()
            end_time = start + 30.0
            continue
        bytes_total += len(in_data)
        del in_data
    end = time.time()
    elapsed = end - start
    error_logger.info("Done. Took {} seconds".format(elapsed))
    error_logger.info("{} bytes in 30 seconds = {}".format(bytes_total, (bytes_total/30.0)))

@app.websocket('/benchp')
async def bench_p_time(request, ws):
    i = 0
    bytes_total = 0
    real_start = 0
    start_ptime = 0
    end_ptime = 0
    started = False
    await ws.send("1")
    while started is False or (end_ptime > time.process_time()):
        i += 1
        in_data = await ws.recv()
        if started is False:
            del in_data
            error_logger.info("received first data: starting benchmark now..")
            started = True
            real_start = time.time()
            start_ptime = time.process_time()
            end_ptime = start_ptime + 30.0
            continue
        bytes_total += len(in_data)
        del in_data
    real_end = time.time()
    elapsed = real_end - real_start
    error_logger.info("Done. Took {} seconds".format(elapsed))
    error_logger.info("{} bytes in 30 seconds = {}".format(bytes_total, (bytes_total/30.0)))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=False, auto_reload=False)

