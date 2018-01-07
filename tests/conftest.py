import re
import sanic


def pytest_collection_modifyitems(session, config, items):
    base_port = sanic.testing.PORT

    worker_id = getattr(config, 'slaveinput', {}).get('slaveid', 'master')
    m = re.search(r'[0-9]+', worker_id)
    if m:
        num_id = int(m.group(0)) + 1
    else:
        num_id = 0
    new_port = base_port + num_id

    def new_test_client(app, port=new_port):
        return sanic.testing.SanicTestClient(app, port)

    sanic.Sanic.test_port = new_port
    sanic.Sanic.test_client = property(new_test_client)

    app = sanic.Sanic()
    assert app.test_client.port == new_port
