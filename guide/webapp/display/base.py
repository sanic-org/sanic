from __future__ import annotations

from html5tagger import Builder, Document  # type: ignore


class BaseRenderer:
    def __init__(self, base_title: str):
        self.base_title = base_title

    def get_builder(self, full: bool, language: str) -> Builder:
        if full:
            urls = [
                "/assets/code.css",
                "/assets/style.css",
                "/assets/docs.js",
                "https://unpkg.com/htmx.org@1.9.2/dist/htmx.min.js",
                "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js",
            ]
            builder = Document(
                self.base_title, lang=language, _urls=urls, _viewport=True
            )
            builder.full = True
            return builder
        else:
            builder = Builder(name="Partial")
            builder.full = False
            return builder
