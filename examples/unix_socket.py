from sanic import Sanic, response


app = Sanic("Example")


@app.route("/test")
async def test(request):
    return response.text("OK")


if __name__ == "__main__":
    app.run(unix="./uds_socket")
