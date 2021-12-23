from sanic import Sanic, response


app = Sanic("Example")


@app.route("/")
async def index(request):
    # generate a URL for the endpoint `post_handler`
    url = app.url_for("post_handler", post_id=5)
    # the URL is `/posts/5`, redirect to it
    return response.redirect(url)


@app.route("/posts/<post_id>")
async def post_handler(request, post_id):
    return response.text("Post - {}".format(post_id))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
