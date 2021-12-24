import asyncio

import uvloop

from sanic import Sanic, response


app = Sanic("Example")


@app.route("/")
async def test(request):
    return response.json({"answer": "42"})


async def main():
    server = await app.create_server(
        port=8000, host="0.0.0.0", return_asyncio_server=True
    )

    if server is None:
        return

    await server.startup()
    await server.serve_forever()


if __name__ == "__main__":
    asyncio.set_event_loop(uvloop.new_event_loop())
    asyncio.run(main())
