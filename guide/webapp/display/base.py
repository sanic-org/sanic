from __future__ import annotations

from os import environ

from html5tagger import Builder, Document, E  # type: ignore


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
                self.title(), lang=language, _urls=urls, _viewport=True
            )
            builder(*self._head())
            builder.full = True
        else:
            builder = Builder(name="Partial")
            builder.full = False
        return builder

    def title(self) -> str:
        return self.base_title

    def _head(self) -> list[Builder]:
        head = [
            E.meta(name="theme-color", content="#ff0d68"),
            E.meta(name="title", content=self.title()),
            E.meta(
                name="description",
                content=(
                    "Sanic is a Python 3.9+ web server and "
                    "web framework that's written to go fast."
                ),
            ),
            E.link(rel="icon", href="/favicon.ico", sizes="any"),
            E.link(rel="icon", href="/favicon-32x32.png", type="image/png"),
            E.link(rel="icon", href="/favicon-16x16.png", type="image/png"),
            E.link(
                rel="apple-touch-icon",
                sizes="180x180",
                href="/apple-touch-icon.png",
            ),
            E.link(rel="manifest", href="/site.webmanifest"),
            E.link(
                rel="android-chrome",
                sizes="192x192",
                href="/android-chrome-192x192.png",
            ),
            E.link(
                rel="android-chrome",
                sizes="512x512",
                href="/android-chrome-512x512.png",
            ),
            E.meta(name="msapplication-config", content="/browserconfig.xml"),
            E.meta(name="msapplication-TileColor", content="#ffffff"),
            E.meta(
                name="msapplication-TileImage", content="/mstile-144x144.png"
            ),
            E.meta(name="theme-color", content="#ff0d68"),
            E.link(
                rel="mask-icon", href="/safari-pinned-tab.svg", color="#ff0d68"
            ),
        ]
        umami = E.script(
            None,
            async_=True,
            defer=True,
            data_website_id="0131e426-4d6d-476b-a84b-34a45e0be6de",
            src="https://analytics.sanicframework.org/umami.js",
        )
        if environ.get("UMAMI"):
            head.append(umami)
        return head
