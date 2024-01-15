# from scss.compiler import compile_string

from pygments.formatters import html
from sass import compile as compile_scss

from sanic import Sanic
from webapp.display.code_style import SanicCodeStyle


def setup_style(app: Sanic) -> None:
    index = app.config.STYLE_DIR / "index.scss"
    style_output = app.config.PUBLIC_DIR / "assets" / "style.css"
    code_output = app.config.PUBLIC_DIR / "assets" / "code.css"

    @app.before_server_start
    async def setup(app: Sanic):
        scss = compile_scss(
            string=index.read_text(),
            include_paths=[
                str(app.config.NODE_MODULES_DIR),
                str(app.config.STYLE_DIR),
            ],
        )
        style_output.write_text(scss)
        formatter = html.HtmlFormatter(
            style=SanicCodeStyle, full=True, cssfile=code_output
        )
        code_output.write_text(formatter.get_style_defs())
