# from urllib.parse import unquote

from sanic import Blueprint, Request, Sanic, html
from webapp.display.page import Page
from webapp.display.search.renderer import SearchRenderer
from webapp.display.search.search import Document, Searcher, Stemmer


bp = Blueprint("search", url_prefix="/<language>/search")


@bp.get("")
async def _search(request: Request, language: str, searcher: Searcher):
    full = not bool(request.headers.get("HX-Request"))
    renderer = SearchRenderer("Sanic Documentation Search")
    builder = renderer.render(request, language, searcher, full)

    return html(str(builder))


@bp.before_server_start
async def setup_search(app: Sanic):
    stemmer = Stemmer()
    pages: list[Page] = app.ctx.pages
    documents = [
        Document(page=page, language=page.meta.language).process(stemmer)
        for page in pages
    ]
    app.ext.dependency(Searcher(stemmer, documents))
