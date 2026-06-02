from types import SimpleNamespace

from sanic import Request, Sanic
from sanic.config import Config
from sanic.response import HTTPResponse, empty


class RouteContainer:
    def setup_routes(self, app: Sanic[Config, SimpleNamespace]) -> None:
        app.get("/api")(self.api)

    async def api(
        self, request: Request[Sanic[Config, SimpleNamespace], SimpleNamespace]
    ) -> HTTPResponse:
        return empty(200)
