from datetime import datetime

from html5tagger import Builder, E  # type: ignore
from sanic import Request


def do_footer(builder: Builder, request: Request) -> None:
    builder.footer(
        _pagination(request),
        _content(),
        class_="footer",
    )


def _pagination(request: Request) -> Builder:
    return E.div(
        _pagination_left(request), _pagination_right(request), class_="level"
    )


def _pagination_left(request: Request) -> Builder:
    item = E.div(class_="level-item")
    if not hasattr(request.ctx, "previous_page"):
        return E.div(item, class_="level-left")
    with item:
        if p := request.ctx.previous_page:
            path = p.relative_path.with_suffix(".html")
            item.a(
                f"← {p.meta.title}",
                href=f"/{path}",
                hx_get=f"/{path}",
                hx_target="#content",
                hx_swap="innerHTML",
                hx_push_url="true",
                class_="button pagination",
            )
    return E.div(item, class_="level-left")


def _pagination_right(request: Request) -> Builder:
    item = E.div(class_="level-item")
    if not hasattr(request.ctx, "next_page"):
        return E.div(item, class_="level-right")
    with item:
        if p := request.ctx.next_page:
            path = p.relative_path.with_suffix(".html")
            item.a(
                f"{p.meta.title} →",
                href=f"/{path}",
                hx_get=f"/{path}",
                hx_target="#content",
                hx_swap="innerHTML",
                hx_push_url="true",
                class_="button pagination",
            )
    return E.div(item, class_="level-right")


def _content() -> Builder:
    year = datetime.now().year
    inner = E.p(
        E.a(
            "MIT Licensed",
            href="https://github.com/sanic-org/sanic/blob/master/LICENSE",
            target="_blank",
            rel="nofollow noopener noreferrer",
        ).br()(
            E.small(f"Copyright © 2018-{year} Sanic Community Organization")
        ),
    )
    return E.div(
        inner,
        E.p("~ Made with ❤️ and ☕️ ~"),
        class_="content has-text-centered",
    )
