from sanic import Blueprint

from .search import bp as search_bp

bp = Blueprint.group(search_bp)
