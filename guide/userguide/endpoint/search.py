from urllib.parse import unquote

from userguide.display.page import Page
from userguide.search.search import Document, Searcher, Stemmer

from sanic import Blueprint, Request, Sanic, html, redirect

bp = Blueprint("search", url_prefix="/search")


@bp.get("")
async def _search(request: Request, searcher: Searcher):
    # Check if not HTMX
    if not request.headers.get("HX-Request"):
        return redirect("/")

    query = unquote(request.args.get("q", ""))
    if query:
        results = searcher.search(query)
        return html(
            f"""
            <h1>Search: {query}</h1>
            <ul>
                {"".join(
                    f"<li><a href='/{doc.page.relative_path}'>{doc.title}</a> - {doc.page.relative_path}</li>"
                    for _, doc in results
                )}
            </ul>
            """
        )

    return html("No results")


@bp.after_server_start
async def setup_search(app: Sanic):
    stemmer = Stemmer()
    pages: list[Page] = app.ctx.pages
    documents = [Document(page=page).process(stemmer) for page in pages]
    app.ext.dependency(Searcher(stemmer, documents))
