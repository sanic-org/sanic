from html5tagger import Builder, E  # type: ignore

from sanic import Request
from webapp.display.layouts.models import MenuItem


def do_navbar(builder: Builder, request: Request) -> None:
    navbar_items = [
        _render_navbar_item(item, request)
        for item in request.app.config.NAVBAR
    ]
    container = E.div(
        _search_form(request), *navbar_items, class_="navbar-end"
    )

    builder.nav(
        E.div(container, class_="navbar-menu"),
        class_="navbar is-hidden-touch",
    )


def _search_form(request: Request) -> Builder:
    return E.div(
        E.div(
            E.input(
                id_="search",
                type_="text",
                placeholder="Search",
                class_="input",
                value=request.args.get("q", ""),
                hx_target="#content",
                hx_swap="innerHTML",
                hx_push_url="true",
                hx_trigger="keyup changed delay:500ms",
                hx_get=f"/{request.ctx.language}/search",
                hx_params="*",
            ),
            class_="control",
        ),
        class_="navbar-item",
    )


def _render_navbar_item(item: MenuItem, request: Request) -> Builder:
    if item.items:
        return E.div(
            E.a(item.label, class_="navbar-link"),
            E.div(
                *(
                    _render_navbar_item(subitem, request)
                    for subitem in item.items
                ),
                class_="navbar-dropdown",
            ),
            class_="navbar-item has-dropdown is-hoverable",
        )

    kwargs = {
        "class_": "navbar-item",
    }
    if item.href:
        kwargs["href"] = item.href
        kwargs["target"] = "_blank"
        kwargs["rel"] = "nofollow noopener noreferrer"
    elif item.path:
        kwargs["href"] = f"/{request.ctx.language}/{item.path}"
    internal = [item.label]
    return E.a(*internal, **kwargs)
