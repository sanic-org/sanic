# import pytest

# from sanic.response import text
# from sanic.router import RouteExists


# @pytest.mark.parametrize(
#     "method,attr, expected",
#     [
#         ("get", "text", "OK1 test"),
#         ("post", "text", "OK2 test"),
#         ("put", "text", "OK2 test"),
#         ("delete", "status", 405),
#     ],
# )
# def test_overload_dynamic_routes(app, method, attr, expected):
#     @app.route("/overload/<param>", methods=["GET"])
#     async def handler1(request, param):
#         return text("OK1 " + param)

#     @app.route("/overload/<param>", methods=["POST", "PUT"])
#     async def handler2(request, param):
#         return text("OK2 " + param)

#     request, response = getattr(app.test_client, method)("/overload/test")
#     assert getattr(response, attr) == expected


# def test_overload_dynamic_routes_exist(app):
#     @app.route("/overload/<param>", methods=["GET"])
#     async def handler1(request, param):
#         return text("OK1 " + param)

#     @app.route("/overload/<param>", methods=["POST", "PUT"])
#     async def handler2(request, param):
#         return text("OK2 " + param)

#     # if this doesn't raise an error, than at least the below should happen:
#     # assert response.text == 'Duplicated'
#     with pytest.raises(RouteExists):

#         @app.route("/overload/<param>", methods=["PUT", "DELETE"])
#         async def handler3(request, param):
#             return text("Duplicated")
