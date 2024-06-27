"""Sanic  User Guide

https://sanic.dev

Built using the SHH stack:
- Sanic
- html5tagger
- HTMX"""

from pathlib import Path

from webapp.worker.factory import create_app


app = create_app(Path(__file__).parent)
