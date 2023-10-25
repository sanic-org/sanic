import re

SLUGIFY_PATTERN = re.compile(r"[^a-zA-Z0-9-]")


def slugify(text: str) -> str:
    return SLUGIFY_PATTERN.sub("", text.lower().replace(" ", "-"))
