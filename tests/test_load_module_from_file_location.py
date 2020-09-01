from pathlib import Path
from types import ModuleType

from pytest import raises as pytest_raises

from sanic.exceptions import LoadFileException
from sanic.utils import load_module_from_file_location


def test_load_module_from_file_location():
    assert isinstance(
        load_module_from_file_location(
            Path(__file__).parent / "static/app_conf.py"),
        ModuleType)


def test_load_module_from_file_location_with_non_existing_env_variable():
    with pytest_raises(
        LoadFileException,
        match="The following environment variables are not set: {MuuMilk}"):

        load_module_from_file_location("${MuuMilk}")
