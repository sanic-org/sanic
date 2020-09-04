from pathlib import Path

import pytest



@pytest.mark.parametrize(
    "conf_object",
    [{"A": 1},
     type("C", (), {"A": 1}),
     pytest.param(str(Path(__file__).parent / "static/app_conf.py"),
                  marks=pytest.mark.dependency(
                      depends=["test_load_module_from_file_location"],
                      scope="session"))],
    ids=["from_dict", "from_class", "from_file"])
def test_update(app, conf_object):
    app.update_config(conf_object)
    assert app.config["A"] == 1



def test_update_from_lowercase_key(app):
    d = {"b": 1}
    app.update_config(d)
    assert "b" not in app.config
