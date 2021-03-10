from sanic import Sanic, response
from sanic.blueprints import Blueprint


# Usage
# curl -H "Host: example.com" localhost:8000
# curl -H "Host: sub.example.com" localhost:8000
# curl -H "Host: bp.example.com" localhost:8000/question
# curl -H "Host: bp.example.com" localhost:8000/answer

app = Sanic(__name__)
bp = Blueprint("bp", host="bp.example.com")


@app.route(
    "/", host=["example.com", "somethingelse.com", "therestofyourdomains.com"]
)
async def hello_0(request):
    return response.text("Some defaults")


@app.route("/", host="sub.example.com")
async def hello_1(request):
    return response.text("42")


@bp.route("/question")
async def hello_2(request):
    return response.text("What is the meaning of life?")


@bp.route("/answer")
async def hello_3(request):
    return response.text("42")


@app.get("/name")
def name(request):
    return response.text(request.app.url_for("name", _external=True))


app.blueprint(bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
