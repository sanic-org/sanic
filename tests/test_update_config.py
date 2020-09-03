# WORK IN Progress


#from pathlib import Path
#
#from pytest import fixture as pytest_fixture
#
#from sanic import Sanic
#
#
#@pytest_fixture
#def sanic_app():
#    return Sanic()
#
#
#@pytest_fixture(
#    params=[
#        {"A": 1},
#        type("C", (), {"A": 1}),
#        Path(__file__).parent / "static/app_conf.py",
#    ],
#    ids=["from_dict", "from_class", "from_file"],
#)
#def conf_object(request):
#    return request.param
#
#
## test_load_module_from_file_location
## scope="session"
#@pytest.mark.parametrize("sanic_app,conf_object",
#                         [(Sanic(), {"A": 1},),
#                          (Sanic(), type("C", (), {"A": 1})),
#                          (Sanic(), Path(__file__).parent / "static/app_conf.py")],
#                         ids=["from_dict", "from_class", "from_file"])
#def test_update(sanic_app, conf_object):
#    sanic_app.update_config(conf_object)
#    assert sanic_app.config["A"] == 1
#
#
#def test_update_from_lowercase_key(sanic_app):
#    d = {"b": 1}
#    sanic_app.update_config(d)
#    assert "b" not in sanic_app.config
