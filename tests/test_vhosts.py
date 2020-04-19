from sanic.response import text


def test_vhosts(app):
    @app.route("/", host="example.com")
    async def handler1(request):
        return text("You're at example.com!")

    @app.route("/", host="subdomain.example.com")
    async def handler2(request):
        return text("You're at subdomain.example.com!")

    headers = {"Host": "example.com"}
    request, response = app.test_client.get("/", headers=headers)
    assert response.text == "You're at example.com!"

    headers = {"Host": "subdomain.example.com"}
    request, response = app.test_client.get("/", headers=headers)
    assert response.text == "You're at subdomain.example.com!"


def test_vhosts_with_list(app):
    @app.route("/", host=["hello.com", "world.com"])
    async def handler(request):
        return text("Hello, world!")

    headers = {"Host": "hello.com"}
    request, response = app.test_client.get("/", headers=headers)
    assert response.text == "Hello, world!"

    headers = {"Host": "world.com"}
    request, response = app.test_client.get("/", headers=headers)
    assert response.text == "Hello, world!"


def test_vhosts_with_defaults(app):
    @app.route("/", host="hello.com")
    async def handler1(request):
        return text("Hello, world!")

    @app.route("/")
    async def handler2(request):
        return text("default")

    headers = {"Host": "hello.com"}
    request, response = app.test_client.get("/", headers=headers)
    assert response.text == "Hello, world!"

    request, response = app.test_client.get("/")
    assert response.text == "default"
