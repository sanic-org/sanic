from pathlib import Path
from types import ModuleType

import pytest

from sanic.exceptions import LoadFileException
from sanic.utils import load_module_from_file_location


@pytest.fixture
def loaded_module_from_file_location():
    return load_module_from_file_location(
        str(Path(__file__).parent / "static" / "app_test_config.py")
    )


@pytest.mark.dependency(name="test_load_module_from_file_location")
def test_load_module_from_file_location(loaded_module_from_file_location):
    assert isinstance(loaded_module_from_file_location, ModuleType)


@pytest.mark.dependency(depends=["test_load_module_from_file_location"])
def test_loaded_module_from_file_location_name(
    loaded_module_from_file_location,
):
    name = loaded_module_from_file_location.__name__
    if "C:\\" in name:
        name = name.split("\\")[-1]
    assert name == "app_test_config"


def test_load_module_from_file_location_with_non_existing_env_variable():
    with pytest.raises(
        LoadFileException,
        match="The following environment variables are not set: MuuMilk",
    ):

        load_module_from_file_location("${MuuMilk}")
