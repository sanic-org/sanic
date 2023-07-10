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
        label="Reference",
        items=[
            MenuItem(
                label="API Documentation",
                href="https://sanic.readthedocs.io/en/stable/",
            )
        ],
    ),
]
