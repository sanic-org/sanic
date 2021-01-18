from os import environ
from pathlib import Path
from types import ModuleType

import pytest

from sanic.exceptions import LoadFileException
from sanic.utils import load_module_from_file_location


@pytest.mark.parametrize(
    "location",
    (
        Path(__file__).parent / "static" / "app_test_config.py",
        str(Path(__file__).parent / "static" / "app_test_config.py"),
        str(Path(__file__).parent / "static" / "app_test_config.py").encode(),
    ),
)
def test_load_module_from_file_location(location):
    module = load_module_from_file_location(location)

    assert isinstance(module, ModuleType)


def test_loaded_module_from_file_location_name():
    module = load_module_from_file_location(
        str(Path(__file__).parent / "static" / "app_test_config.py")
    )

    name = module.__name__
    if "C:\\" in name:
        name = name.split("\\")[-1]
    assert name == "app_test_config"


def test_load_module_from_file_location_with_non_existing_env_variable():
    with pytest.raises(
        LoadFileException,
        match="The following environment variables are not set: MuuMilk",
    ):

        load_module_from_file_location("${MuuMilk}")


def test_load_module_from_file_location_using_env():
    environ["APP_TEST_CONFIG"] = "static/app_test_config.py"
    location = str(Path(__file__).parent / "${APP_TEST_CONFIG}")
    module = load_module_from_file_location(location)

    assert isinstance(module, ModuleType)
