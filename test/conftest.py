import pytest
import sugartrail.api


def pytest_addoption(parser):
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests against the real Companies House API",
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--integration"):
        skip = pytest.mark.skip(reason="pass --integration to run API tests")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip)


@pytest.fixture
def no_auth():
    """Ensure basic_auth has no username for tests that check unauthenticated behaviour.
    Restores the original value after the test."""
    original = sugartrail.api.basic_auth.username
    sugartrail.api.basic_auth.username = ""
    yield
    sugartrail.api.basic_auth.username = original


@pytest.fixture
def mock_auth():
    """Set a fake API key so auth checks pass without real credentials."""
    original = sugartrail.api.basic_auth.username
    sugartrail.api.basic_auth.username = "fake_api_key"
    yield
    sugartrail.api.basic_auth.username = original
