"""
Root conftest.py for all test categories.

Provides shared fixtures for contract, integration, and performance tests.
"""

import asyncio
import importlib
import os
import sys
import tempfile
from pathlib import Path
from typing import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def backend_src_path() -> Path:
    """Get the backend src directory path."""
    return Path(__file__).resolve().parents[1] / "src"


@pytest.fixture(scope="session", autouse=True)
def setup_import_path():
    """Add src directory to Python path for all tests."""
    src_path = str(backend_src_path())
    if src_path not in sys.path:
        sys.path.insert(0, src_path)


@pytest.fixture(scope="session")
def test_database_url():
    """Create a temporary database for testing."""
    # Use in-memory SQLite for tests
    return "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine(test_database_url):
    """Create test database engine."""
    from sqlalchemy import create_engine

    engine = create_engine(
        test_database_url,
        connect_args={"check_same_thread": False},  # Needed for SQLite
    )
    return engine


@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    """Create test session factory."""
    from sqlalchemy.orm import sessionmaker

    TestSession = sessionmaker(bind=test_engine)
    return TestSession


@pytest.fixture(scope="function")
def test_session(test_engine, test_session_factory):
    """Create a test database session with tables."""
    # Import models package to register metadata before creation
    import importlib

    required_models = [
        "domains.users.models.user",
        "domains.users.models.user_preference",
        "domains.sports.models.player",
        "domains.scoring.models.score",
        "domains.drafts.models.draft",
        "domains.leagues.models.league",
        "domains.leagues.models.league_branding",
        "domains.leagues.models.team",
        "domains.lineups.models.lineup",
        "domains.trading.models.trade",
        "domains.trading.models.waiver",
        "domains.trading.models.transaction",
        "domains.shared.models.achievement",
        "domains.waitlist.models.waitlist",
    ]

    for module in required_models:
        importlib.import_module(module)
    from domains.shared.models.base import Base

    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    # Create session
    session = test_session_factory()

    try:
        yield session
    finally:
        session.close()
        # Clean up tables after each test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def app():
    """Create FastAPI app instance for testing."""
    # Import main app
    app_module = importlib.import_module("main")
    assert hasattr(app_module, "app"), "Expected 'app' FastAPI instance in main.py"
    return app_module.app


@pytest.fixture
def client(app):
    """Create FastAPI test client."""
    return TestClient(app)


# Service fixtures with proper dependency injection
@pytest.fixture
def league_service(test_session):
    """Create LeagueService with test database session."""
    from domains.leagues.services.league_service import LeagueService

    return LeagueService(session=test_session)


@pytest.fixture
def user_service(test_session):
    """Create UserService with test database session."""
    from domains.users.services.user_service import UserService

    return UserService(session=test_session)


@pytest.fixture
def lineup_service(test_session):
    """Create LineupService with test database session."""
    from domains.lineups.services.lineup_service import LineupService

    return LineupService(session=test_session)


@pytest.fixture
def scoring_service(test_session):
    """Create ScoringService with test database session."""
    from domains.scoring.services.scoring_service import ScoringService

    return ScoringService(session=test_session)


@pytest.fixture
def trading_service(test_session):
    """Create TradingService with test database session."""
    from domains.trading.services.trading_service import TradingService

    return TradingService(session=test_session)


@pytest.fixture
def waitlist_service(test_session):
    """Create WaitlistService with test database session."""
    from domains.waitlist.services.waitlist_service import WaitlistService

    return WaitlistService(db_session=test_session)


# Mock the container for tests that need it
@pytest.fixture
def mock_container(test_session):
    """Mock container for dependency injection in tests."""

    class MockContainer:
        async def health_check(self):
            return {"status": "healthy", "database": "connected"}

        def get_service_registry(self):
            class MockRegistry:
                def health_check(self):
                    return {"status": "healthy", "services": []}

            return MockRegistry()

        def get_configuration(self):
            return {"test_mode": True}

    return MockContainer()


# Performance testing fixtures
@pytest.fixture
def benchmark_config():
    """Configuration for benchmark tests."""
    return {"min_rounds": 5, "max_time": 1.0, "warmup": False}
