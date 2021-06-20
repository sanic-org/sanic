import logging

from sanic.touchup import TouchUp


def test_touchup_methods(app):
    assert len(TouchUp._registry) == 9


def test_touchup_removes_ode(app, caplog):
    with caplog.at_level(logging.DEBUG):
        TouchUp.run(app)

    print(caplog.record_tuples)
    assert ("sanic.root", logging.DEBUG, "...") in caplog.record_tuples
