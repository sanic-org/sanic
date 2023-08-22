from userguide.display.layouts.models import MenuItem

NAVBAR = [
    MenuItem(
        label="Home",
        path="index.html",
    ),
    MenuItem(
        label="Community",
        items=[
            MenuItem(
                label="Forums",
                href="https://community.sanicframework.org",
            ),
            MenuItem(
                label="Discord",
                href="https://discord.gg/FARQzAEMAA",
            ),
            MenuItem(
                label="Twitter",
                href="https://twitter.com/sanicframework",
            ),
        ],
    ),
    MenuItem(
        label="Help",
        path="index.html",
    ),
    MenuItem(label="GitHub", href="https://github.com/sanic-org/sanic"),
]


SIDEBAR = [
    MenuItem(
        label="User Guide",
        items=[
            MenuItem(
                label="General",
                items=[
                    MenuItem(
                        label="Introduction",
                        path="guide/introduction.html",
                    ),
                    MenuItem(
                        label="Getting Started",
                        path="guide/getting-started.html",
                    ),
                ],
            ),
            MenuItem(
                label="Basics",
                items=[
                    MenuItem(
                        label="Sanic Application",
                        path="guide/basics/app.html",
                    ),
                ],
            ),
            MenuItem(
                label="Advanced",
                items=[
                    MenuItem(
                        label="Class Based Views",
                        path="guide/advanced/class-based-views.html",
                    ),
                ],
            ),
            MenuItem(
                label="Best Practices",
                items=[
                    MenuItem(
                        label="Blueprints",
                        path="guide/best-practices/blueprints.html",
                    ),
                ],
            ),
            MenuItem(
                label="Running Sanic",
                items=[
                    MenuItem(
                        label="Configuration",
                        path="guide/running/configuration.html",
                    ),
                ],
            ),
            MenuItem(
                label="Deployment",
                items=[
                    MenuItem(
                        label="Docker",
                        path="guide/deployment/docker.html",
                    ),
                ],
            ),
            MenuItem(
                label="How to ...",
                items=[
                    MenuItem(
                        label="Table of Contents",
                        path="guide/how-to/table-of-contents.html",
                    ),
                ],
            ),
        ],
    ),
    MenuItem(
        label="Plugins",
        items=[
            MenuItem(
                label="Sanic Extensions",
                items=[
                    MenuItem(
                        label="Getting Started",
                        path="plugins/sanic-ext/getting-started.html",
                    ),
                ],
            ),
            MenuItem(
                label="Sanic Testing",
                items=[
                    MenuItem(
                        label="Getting Started",
                        path="plugins/sanic-testing/getting-started.html",
                    ),
                ],
            ),
        ],
    ),
    MenuItem(
        label="Release Notes",
        items=[
            MenuItem(
                label="2023",
                items=[
                    MenuItem(
                        label="Sanic 21.3",
                        path="release-notes/21.3.html",
                    ),
                ],
            ),
            MenuItem(
                label="2022",
                items=[
                    MenuItem(
                        label="Sanic 21.3",
                        path="release-notes/21.3.html",
                    ),
                ],
            ),
            MenuItem(
                label="2021",
                items=[
                    MenuItem(
                        label="Sanic 21.3",
                        path="release-notes/21.3.html",
                    ),
                ],
            ),
        ],
    ),
    MenuItem(
        label="Organization",
        items=[
            MenuItem(
                label="Contributing",
                path="organization/contributing.html",
            ),
            MenuItem(
                label="Code of Conduct",
                path="organization/code-of-conduct.html",
            ),
            MenuItem(
                label="Governance",
                path="organization/governance.html",
            ),
            MenuItem(
                label="Security",
                path="organization/security.html",
            ),
        ],
    ),
    MenuItem(
        label="API Reference",
        items=[
            MenuItem(
                label="Application",
                items=[
                    MenuItem(label="sanic.app", path="/api/sanic.app.html"),
                    MenuItem(
                        label="sanic.config", path="/api/sanic.config.html"
                    ),
                    MenuItem(
                        label="sanic.application",
                        path="/api/sanic.application.html",
                    ),
                ],
            ),
            MenuItem(
                label="Blueprint",
                items=[
                    MenuItem(
                        label="sanic.blueprints",
                        path="/api/sanic.blueprints.html",
                    ),
                    MenuItem(
                        label="sanic.blueprint_group",
                        path="/api/sanic.blueprint_group.html",
                    ),
                ],
            ),
            MenuItem(
                label="Constant",
                items=[
                    MenuItem(
                        label="sanic.constants",
                        path="/api/sanic.constants.html",
                    ),
                ],
            ),
            MenuItem(
                label="Core",
                items=[
                    MenuItem(
                        label="sanic.cookies", path="/api/sanic.cookies.html"
                    ),
                    MenuItem(
                        label="sanic.handlers", path="/api/sanic.handlers.html"
                    ),
                    MenuItem(
                        label="sanic.headers", path="/api/sanic.headers.html"
                    ),
                    MenuItem(
                        label="sanic.middleware",
                        path="/api/sanic.middleware.html",
                    ),
                    MenuItem(
                        label="sanic.mixins", path="/api/sanic.mixins.html"
                    ),
                    MenuItem(
                        label="sanic.request", path="/api/sanic.request.html"
                    ),
                    MenuItem(
                        label="sanic.response", path="/api/sanic.response.html"
                    ),
                    MenuItem(
                        label="sanic.views", path="/api/sanic.views.html"
                    ),
                ],
            ),
            MenuItem(
                label="Display",
                items=[
                    MenuItem(
                        label="sanic.pages", path="/api/sanic.pages.html"
                    ),
                ],
            ),
            MenuItem(
                label="Exception",
                items=[
                    MenuItem(
                        label="sanic.errorpages",
                        path="/api/sanic.errorpages.html",
                    ),
                    MenuItem(
                        label="sanic.exceptions",
                        path="/api/sanic.exceptions.html",
                    ),
                ],
            ),
            MenuItem(
                label="Model",
                items=[
                    MenuItem(
                        label="sanic.models", path="/api/sanic.models.html"
                    ),
                ],
            ),
            MenuItem(
                label="Routing",
                items=[
                    MenuItem(
                        label="sanic.router", path="/api/sanic.router.html"
                    ),
                    MenuItem(
                        label="sanic.signals", path="/api/sanic.signals.html"
                    ),
                ],
            ),
            MenuItem(
                label="Server",
                items=[
                    MenuItem(label="sanic.http", path="/api/sanic.http.html"),
                    MenuItem(
                        label="sanic.server", path="/api/sanic.server.html"
                    ),
                    MenuItem(
                        label="sanic.worker", path="/api/sanic.worker.html"
                    ),
                ],
            ),
            MenuItem(
                label="Utility",
                items=[
                    MenuItem(
                        label="sanic.compat", path="/api/sanic.compat.html"
                    ),
                    MenuItem(
                        label="sanic.helpers", path="/api/sanic.helpers.html"
                    ),
                    MenuItem(label="sanic.log", path="/api/sanic.log.html"),
                    MenuItem(
                        label="sanic.utils", path="/api/sanic.utils.html"
                    ),
                ],
            ),
        ],
    ),
]
