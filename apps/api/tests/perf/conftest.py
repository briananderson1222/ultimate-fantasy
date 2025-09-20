"""Shared fixtures for performance tests."""

import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def backend_src_path() -> Path:
    return Path(__file__).resolve().parents[2] / "src"


@pytest.fixture
def client() -> TestClient:
    """Create a test client with proper database setup."""
    sys.path.insert(0, str(backend_src_path()))

    # Import and setup database
    from domains.shared.models.base import Base
    from infrastructure.database.session_factory import get_session_factory

    # Create tables
    session_factory = get_session_factory()
    if session_factory._engine:
        Base.metadata.create_all(bind=session_factory._engine)

    # Import app and create client
    app_module = importlib.import_module("main")
    assert hasattr(
        app_module, "app"
    ), "Expected FastAPI instance named 'app' in main.py"

    return TestClient(app_module.app)
