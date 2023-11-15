from pathlib import Path

from msgspec import yaml

from webapp.display.layouts.models import GeneralConfig, MenuItem


def load_menu(path: Path) -> list[MenuItem]:
    loaded = yaml.decode(path.read_bytes(), type=dict[str, list[MenuItem]])
    return loaded["root"]


def load_config(path: Path) -> GeneralConfig:
    loaded = yaml.decode(path.read_bytes(), type=GeneralConfig)
    return loaded
