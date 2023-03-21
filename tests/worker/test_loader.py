import sys

from os import getcwd
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from sanic.app import Sanic
from sanic.worker.loader import AppLoader, CertLoader


STATIC = Path.cwd() / "tests" / "static"


@pytest.mark.parametrize(
    "module_input", ("tests.fake.server:app", "tests.fake.server.app")
)
def test_load_app_instance(module_input):
    loader = AppLoader(module_input)
    app = loader.load()
    assert isinstance(app, Sanic)


@pytest.mark.parametrize(
    "module_input",
    ("tests.fake.server:create_app", "tests.fake.server:create_app()"),
)
def test_load_app_factory(module_input):
    loader = AppLoader(module_input, as_factory=True)
    app = loader.load()
    assert isinstance(app, Sanic)


def test_load_app_simple():
    loader = AppLoader(str(STATIC), as_simple=True)
    app = loader.load()
    assert isinstance(app, Sanic)


def test_create_with_factory():
    loader = AppLoader(factory=lambda: Sanic("Test"))
    app = loader.load()
    assert isinstance(app, Sanic)


def test_cwd_in_path():
    AppLoader("tests.fake.server:app").load()
    assert getcwd() in sys.path


def test_input_is_dir():
    loader = AppLoader(str(STATIC))
    app = loader.load()
    assert isinstance(app, Sanic)


def test_input_is_factory():
    ns = SimpleNamespace(target="foo")
    loader = AppLoader("tests.fake.server:create_app", args=ns)
    app = loader.load()
    assert isinstance(app, Sanic)


def test_input_is_module():
    ns = SimpleNamespace(target="foo")
    loader = AppLoader("tests.fake.server", args=ns)

    app = loader.load()
    assert isinstance(app, Sanic)


@pytest.mark.parametrize("creator", ("mkcert", "trustme"))
@patch("sanic.worker.loader.TrustmeCreator")
@patch("sanic.worker.loader.MkcertCreator")
def test_cert_loader(MkcertCreator: Mock, TrustmeCreator: Mock, creator: str):
    CertLoader._creators = {
        "mkcert": MkcertCreator,
        "trustme": TrustmeCreator,
    }
    MkcertCreator.return_value = MkcertCreator
    TrustmeCreator.return_value = TrustmeCreator
    data = {
        "creator": creator,
        "key": Path.cwd() / "tests" / "certs" / "localhost" / "privkey.pem",
        "cert": Path.cwd() / "tests" / "certs" / "localhost" / "fullchain.pem",
        "localhost": "localhost",
    }
    app = Sanic("Test")
    loader = CertLoader(data)  # type: ignore
    loader.load(app)
    creator_class = MkcertCreator if creator == "mkcert" else TrustmeCreator
    creator_class.assert_called_once_with(app, data["key"], data["cert"])
    creator_class.generate_cert.assert_called_once_with("localhost")
