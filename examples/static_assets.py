from sanic import Sanic


app = Sanic(__name__)

app.static("/", "./static")
