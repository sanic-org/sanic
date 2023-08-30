import re
from pathlib import Path
from textwrap import indent

from emoji import EMOJI

COLUMN_PATTERN = re.compile(r"---:1\s*(.*?)\s*:--:1\s*(.*?)\s*:---", re.DOTALL)
PYTHON_HIGHLIGHT_PATTERN = re.compile(r"```python\{+.*?\}", re.DOTALL)
BASH_HIGHLIGHT_PATTERN = re.compile(r"```bash\{+.*?\}", re.DOTALL)
NOTIFICATION_PATTERN = re.compile(
    r":::\s*(\w+)\s*(.*?)\n([\s\S]*?):::", re.MULTILINE
)
EMOJI_PATTERN = re.compile(r":(\w+):")
CURRENT_DIR = Path(__file__).parent
SOURCE_DIR = (
    CURRENT_DIR.parent.parent.parent.parent / "sanic-guide" / "src" / "en"
)


def convert_columns(content: str):
    def replacer(match: re.Match):
        left, right = match.groups()
        left = indent(left.strip(), " " * 4)
        right = indent(right.strip(), " " * 4)
        return f"""
.. column::

{left}

.. column::

{right}
"""

    return COLUMN_PATTERN.sub(replacer, content)


def cleanup_highlights(content: str):
    content = PYTHON_HIGHLIGHT_PATTERN.sub("```python", content)
    content = BASH_HIGHLIGHT_PATTERN.sub("```bash", content)
    return content


def convert_notifications(content: str):
    def replacer(match: re.Match):
        type_, title, body = match.groups()
        body = indent(body.strip(), " " * 4)
        return f"""

.. {type_}:: {title}

{body}

"""

    return NOTIFICATION_PATTERN.sub(replacer, content)


def convert_emoji(content: str):
    def replace(match):
        return EMOJI.get(match.group(1), match.group(0))

    return EMOJI_PATTERN.sub(replace, content)


def convert_code_blocks(content: str):
    for src, dest in (
        ("yml", "yaml"),
        ("caddy", ""),
        ("systemd", ""),
        ("mermaid", "\nmermaid"),
    ):
        content = content.replace(f"```{src}", f"```{dest}")
    return content


def cleanup_multibreaks(content: str):
    return content.replace("\n\n\n", "\n\n")


def convert(content: str):
    content = convert_emoji(content)
    content = convert_columns(content)
    content = cleanup_highlights(content)
    content = convert_code_blocks(content)
    content = convert_notifications(content)
    content = cleanup_multibreaks(content)
    return content


def convert_file(src: Path, dest: Path):
    short_src = src.relative_to(SOURCE_DIR)
    short_dest = dest.relative_to(CURRENT_DIR)
    print(f"Converting {short_src} -> {short_dest}")
    content = src.read_text()
    new_content = convert(content)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.touch()
    dest.write_text(new_content)


def translate_path(source_dir: Path, source_path: Path, dest_dir: Path):
    rel_path = source_path.relative_to(source_dir)
    dest_path = dest_dir / rel_path
    return dest_path


def main():
    print(f"Source: {SOURCE_DIR}")

    for path in SOURCE_DIR.glob("**/*.md"):
        if path.name in ("index.md", "README.md"):
            continue
        dest_path = translate_path(SOURCE_DIR, path, CURRENT_DIR)
        convert_file(path, dest_path)


if __name__ == "__main__":
    main()
