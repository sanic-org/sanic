from abc import ABCMeta
from pathlib import Path
from typing import Optional


CURRENT_DIR = Path(__file__).parent

branch_coverage = {
    "cssBranch1": False,  
    "cssBranch2": False,
    "cssBranch3": False,
    "cssBranch4": False,
    "cssBranch5": False,
    "cssBranch6": False,
}

def _extract_style(maybe_style: Optional[str], name: str) -> str:
    if maybe_style is not None:
        branch_coverage["cssBranch1"] = True
        maybe_path = Path(maybe_style)
        if maybe_path.exists():
            branch_coverage["cssBranch2"] = True
            return maybe_path.read_text(encoding="UTF-8")
        branch_coverage["cssBranch3"] = True
        return maybe_style
    branch_coverage["cssBranch4"] = True
    maybe_path = CURRENT_DIR / "styles" / f"{name}.css"
    if maybe_path.exists():
        branch_coverage["cssBranch5"] = True
        return maybe_path.read_text(encoding="UTF-8")
    branch_coverage["cssBranch6"] = True
    return ""


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
