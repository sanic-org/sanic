from sanic.worker.loader import AppLoader


class AppContainer:
    def __init__(self, loader: AppLoader) -> None:
        self.loader = loader

    def prepare(self, *apps) -> None:
        for app in apps:
            app.prepare(**app._early_prepare)

    def serve(self) -> None:
        from sanic import Sanic

        primary = self.loader.load()
        self.prepare(primary)
        Sanic.serve(primary=primary, app_loader=self.loader)
