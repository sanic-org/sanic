Sockets
=======

Sanic can use the python
`socket module <https://docs.python.org/3/library/socket.html>`_ to accommodate
non IPv4 sockets.

IPv6 example:

.. code:: python

    from sanic import Sanic
    from sanic.response import json
    import socket

    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    sock.bind(('::', 7777))

    app = Sanic()


    @app.route("/")
    async def test(request):
        return json({"hello": "world"})

    if __name__ == "__main__":
        app.run(sock=sock)

to test IPv6 ``curl -g -6 "http://[::1]:7777/"``


UNIX socket example:

.. code:: python

    import signal
    import sys
    import socket
    import os
    from sanic import Sanic
    from sanic.response import json


    server_socket = '/tmp/sanic.sock'

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(server_socket)

    app = Sanic()


    @app.route("/")
    async def test(request):
        return json({"hello": "world"})


    def signal_handler(sig, frame):
            print('Exiting')
            os.unlink(server_socket)
            sys.exit(0)


    if __name__ == "__main__":
        app.run(sock=sock)

to test UNIX: ``curl -v --unix-socket /tmp/sanic.sock http://localhost/hello``
