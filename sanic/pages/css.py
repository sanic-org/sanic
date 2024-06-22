from abc import ABCMeta
from pathlib import Path
from typing import Optional


CURRENT_DIR = Path(__file__).parent

extract_style_branch = {
    "maybe_style_provided": False,  
    "maybe_path_exists": False,
    "return_maybe_style": False,
    "maybe_style_not_provided": False,
    "maybe_path": False,
    "no_maybe_path": False,
}

def _extract_style(maybe_style: Optional[str], name: str) -> str:
    if maybe_style is not None:
        extract_style_branch["maybe_style_provided"] = True
        maybe_path = Path(maybe_style)
        if maybe_path.exists():
            extract_style_branch["maybe_path_exists"] = True
            return maybe_path.read_text(encoding="UTF-8")
        extract_style_branch["return_maybe_style"] = True
        return maybe_style
    extract_style_branch["maybe_style_not_provided"] = True
    maybe_path = CURRENT_DIR / "styles" / f"{name}.css"
    if maybe_path.exists():
        extract_style_branch["maybe_path"] = True
        return maybe_path.read_text(encoding="UTF-8")
    extract_style_branch["no_maybe_path"] = True
    return ""

def print_extract_style_coverage():
    for branch, hit in extract_style_branch.items():
        print(f"{branch} was {'hit' if hit else 'not hit'}")


class CSS(ABCMeta):
    """Cascade stylesheets, i.e. combine all ancestor styles"""

    def __new__(cls, name, bases, attrs):
        Page = super().__new__(cls, name, bases, attrs)
        # Use a locally defined STYLE or the one from styles directory
        Page.STYLE = _extract_style(attrs.get("STYLE_FILE"), name)
        Page.STYLE += attrs.get("STYLE_APPEND", "")
        # Combine with all ancestor styles
        Page.CSS = "".join(
            Class.STYLE
            for Class in reversed(Page.__mro__)
            if type(Class) is CSS
        )
        return Page
