"""
Modify header or status in response
"""

from sanic import Sanic, response


app = Sanic("Example")


@app.route("/")
def handle_request(request):
    return response.json(
        {"message": "Hello world!"},
        headers={"X-Served-By": "sanic"},
        status=200,
    )


@app.route("/unauthorized")
def handle_request(request):
    return response.json(
        {"message": "You are not authorized"},
        headers={"X-Served-By": "sanic"},
        status=404,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
