import sys
import os
import pytest

# Add the project's root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 1. Import the factory function, NOT the app variable
from app import create_app


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""

    # 2. Call the factory to create the app
    flask_app = create_app()

    # 3. Configure it for testing
    flask_app.config.update(
        {
            "TESTING": True,
        }
    )

    # 4. Yield it to the tests
    yield flask_app


# (The client and runner fixtures are unchanged and will work perfectly)
@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()
