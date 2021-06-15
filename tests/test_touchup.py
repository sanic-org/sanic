from sanic.touchup import TouchUp


def test_touchup_methods(app):
    assert len(TouchUp._registry) == 7
