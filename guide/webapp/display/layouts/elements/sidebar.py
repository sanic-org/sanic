from webapp.display.layouts.models import MenuItem
from webapp.display.text import slugify

from html5tagger import Builder, E  # type: ignore
from sanic import Request


def do_sidebar(builder: Builder, request: Request) -> None:
    builder.a(class_="burger")(E.span().span().span().span())
    builder.aside(*_menu_items(request), class_="menu")


def _menu_items(request: Request) -> list[Builder]:
    return [
        _sanic_logo(request),
        *_sidebar_items(request),
        E.hr(),
        E.p("Current with version ").strong(
            request.app.config.GENERAL.current_version
        ),
        E.hr(),
        E.p("Need ").a("help", href=f"/{request.ctx.language}/help.html")("?"),
        E.hr(),
        E.p("Want more? ").a(
            "sanicbook.com", href="https://sanicbook.com", target="_blank"
        ),
    ]


def _sanic_logo(request: Request) -> Builder:
    return E.a(
        class_="navbar-item sanic-simple-logo",
        href=f"https://sanic.dev/{request.ctx.language}/",
    )(
        E.img(
            src="/assets/images/sanic-framework-logo-simple-400x97.png",  # noqa: E501
            alt="Sanic Framework",
        )
    )


def _sidebar_items(request: Request) -> list[Builder]:
    return [
        builder
        for item in request.app.config.SIDEBAR
        for builder in _render_sidebar_item(item, request, True)
    ]


def _render_sidebar_item(
    item: MenuItem, request: Request, root: bool = False
) -> list[Builder]:
    builders: list[Builder] = []
    if root:
        builders.append(E.p(class_="menu-label")(item.label))
    else:
        builders.append(_single_sidebar_item(item, request))

    if item.items:
        ul = E.ul(class_="menu-list")
        with ul:
            for subitem in item.items:
                sub_builders = _render_sidebar_item(subitem, request)
                ul(*sub_builders)
        builders.append(ul)

    return builders


def _single_sidebar_item(item: MenuItem, request: Request) -> Builder:
    if item.path and item.path.startswith("/"):
        path = item.path
    else:
        path = f"/{request.ctx.language}/{item.path}" if item.path else ""
    kwargs = {}
    classes: list[str] = []
    li_classes = "menu-item"
    _, page, _ = request.app.ctx.get_page(
        request.ctx.language, item.path or ""
    )
    if request.path == path:
        classes.append("is-active")
    if item.href:
        kwargs["href"] = item.href
        kwargs["target"] = "_blank"
        kwargs["rel"] = "nofollow noopener noreferrer"
    elif not path:
        li_classes += " is-group"
        if _is_open_item(item, request.ctx.language, request.path):
            classes.append("is-open")
    else:
        kwargs.update(
            {
                "href": path,
                "hx-get": path,
                "hx-target": "#content",
                "hx-swap": "innerHTML",
                "hx-push-url": "true",
            }
        )
    kwargs["class_"] = " ".join(classes)
    inner = E().a(item.label, **kwargs)
    if page and page.anchors:
        with inner.ul(class_="anchor-list"):
            for anchor in page.anchors:
                inner.li(
                    E.a(anchor.strip("`"), href=f"{path}#{slugify(anchor)}"),
                    class_="is-anchor",
                )
    return E.li(inner, class_=li_classes)


def _is_open_item(item: MenuItem, language: str, current_path: str) -> bool:
    path = f"/{language}/{item.path}" if item.path else ""
    if current_path == path:
        return True
    for subitem in item.items:
        if _is_open_item(subitem, language, current_path):
            return True
    return False
