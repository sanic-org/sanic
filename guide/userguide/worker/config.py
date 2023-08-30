from pathlib import Path

from msgspec import yaml
from userguide.display.layouts.models import MenuItem


def load_menu(path: Path) -> list[MenuItem]:
    loaded = yaml.decode(path.read_bytes(), type=dict[str, list[MenuItem]])
    return loaded["root"]
