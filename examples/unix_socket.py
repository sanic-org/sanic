from sanic import Sanic
from sanic import response
import socket
import os

app = Sanic(__name__)


@app.route("/test")
async def test(request):
    return response.text("OK")

if __name__ == '__main__':
    server_address = './uds_socket'
    # Make sure the socket does not already exist
    try:
            os.unlink(server_address)
    except OSError:
            if os.path.exists(server_address):
                        raise
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(server_address)
    app.run(sock=sock)
