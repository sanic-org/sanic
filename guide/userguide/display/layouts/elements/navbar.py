from userguide.display.layouts.models import MenuItem

from html5tagger import Builder, E
from sanic import Request


def do_navbar(builder: Builder, request: Request) -> None:
    navbar_items = [
        _render_navbar_item(item, request)
        for item in request.app.config.NAVBAR
    ]
    container = E.div(*navbar_items, class_="navbar-end")

    builder.nav(
        E.div(container, class_="navbar-menu"),
        class_="navbar is-hidden-touch",
    )


def _render_navbar_item(item: MenuItem, request: Request) -> Builder:
    kwargs = {
        "class_": "navbar-item",
    }
    if item.href:
        kwargs["href"] = item.href
        kwargs["target"] = "_blank"
        kwargs["rel"] = "nofollow noopener noreferrer"
    elif item.path:
        kwargs["href"] = f"/{request.ctx.language}/{item.path}"
    return E.a(item.label, **kwargs)
