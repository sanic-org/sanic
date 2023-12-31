from sanic import Request, Sanic, raw


def setup_sitemap(app: Sanic) -> None:
    app.get("/sitemap.xml")(_sitemap)
    app.before_server_start(_compile_sitemap, priority=0)


async def _compile_sitemap(app: Sanic):
    pages: list[str] = [
        app.url_for(
            "page",
            language="en",
            path=page.relative_path.with_suffix(".html"),
            _external=True,
            _server="sanic.dev",
            _scheme="https",
        )
        for page in app.ctx.pages
        if page.relative_path
    ]
    sitemap_parts: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        *[f"<url><loc>{page}</loc></url>" for page in pages],
        "</urlset>",
    ]
    app.ctx.sitemap = "\n".join(sitemap_parts)


async def _sitemap(request: Request):
    return raw(request.app.ctx.sitemap, content_type="application/xml")
