from pathlib import Path

import pytest


_test_setting_as_dict = {"TEST_SETTING_VALUE": 1}
_test_setting_as_class = type("C", (), {"TEST_SETTING_VALUE": 1})
_test_setting_as_module = str(
    Path(__file__).parent / "static/app_test_config.py"
)


@pytest.mark.parametrize(
    "conf_object",
    [
        _test_setting_as_dict,
        _test_setting_as_class,
        pytest.param(
            _test_setting_as_module,
            marks=pytest.mark.dependency(
                depends=["test_load_module_from_file_location"],
                scope="session",
            ),
        ),
    ],
    ids=["from_dict", "from_class", "from_file"],
)
def test_update(app, conf_object):
    app.update_config(conf_object)
    assert app.config["TEST_SETTING_VALUE"] == 1


def test_update_from_lowercase_key(app):
    d = {"test_setting_value": 1}
    app.update_config(d)
    assert "test_setting_value" not in app.config
