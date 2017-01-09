import asyncio
from sanic import Sanic


def test_bad_request_response():
    app = Sanic('test_bad_request_response')
    lines = []
    async def _request(sanic, loop):
        connect = asyncio.open_connection('127.0.0.1', 42101)
        reader, writer = await connect
        writer.write(b'not http')
        while True:
            line = await reader.readline()
            if not line:
                break
            lines.append(line)
        app.stop()
    app.run(host='127.0.0.1', port=42101, debug=False, after_start=_request)
    assert lines[0] == b'HTTP/1.1 400 Bad Request\r\n'
    assert lines[-1] == b'Error: Bad Request'
