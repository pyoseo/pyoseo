"""pytest configuration file."""

import pytest
from pytest_django.fixtures import live_server


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "unit: run only unit tests"
    )
    config.addinivalue_line(
        "markers",
        "functional: run only functional tests"
    )


def pytest_addoption(parser):
    parser.addoption(
        "--pyoseo-server-url",
        help="URL for a pyoseo server to use when performing "
             "functional tests. If not specified, a local testing server "
             "is spawned, populated and used"
    )
    parser.addoption(
        "--pyoseo-server-user",
        default="user",
        help="Username to use in pyoseo functional tests. Defaults to "
             "%(default)s"
    )
    parser.addoption(
        "--pyoseo-server-password",
        default="pass",
        help="Password to use in pyoseo functional tests. Defaults to "
             "%(default)s"
    )


@pytest.fixture
def pyoseo_server_user(request):
    return request.config.getoption("--pyoseo-server-user")


@pytest.fixture
def pyoseo_server_password(request):
    return request.config.getoption("--pyoseo-server-password")


@pytest.fixture
def pyoseo_server_url(request):
    server_url = request.config.getoption("--pyoseo-server-url")
    if server_url is not None:
        result = server_url
    else:
        server = live_server(request=request)
        result = server.url
    return result

