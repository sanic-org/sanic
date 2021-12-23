from sanic import Sanic


app = Sanic("Example")

app.static("/", "./static")
