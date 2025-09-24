"""
Root conftest.py for all test categories.

Provides shared fixtures for contract, integration, and performance tests.
"""

import asyncio
import importlib
import os
import sys
import tempfile
import uuid
from pathlib import Path
from typing import AsyncGenerator
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
import jwt


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
    import tempfile
    import os

    # Create a temporary database file that both test and app can access
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)  # Close the file descriptor, but keep the file

    # Set environment variable so the app uses the same database
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    yield f"sqlite:///{db_path}"

    # Cleanup
    try:
        os.unlink(db_path)
    except:
        pass


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
def test_user(test_session):
    """Create a test user in the database using user service."""
    from domains.users.services.user_service import UserService

    user_service = UserService(test_session)

    # Create JWT claims that will be used to create the user
    test_claims = {
        "sub": str(uuid.uuid4()),
        "username": "test_user",
        "email": "test@example.com",
        "name": "Test User",
        "given_name": "Test",
        "family_name": "User"
    }

    # Use the ensure_user_from_claims method (the lazy-loaded method you mentioned)
    test_user = user_service.ensure_user_from_claims(test_claims)
    test_session.commit()
    test_session.refresh(test_user)

    return test_user


@pytest.fixture
def test_jwt_token(test_user):
    """Generate a valid JWT token for the test user."""
    # Use same secret as the app (this should match your settings)
    secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
    algorithm = "HS256"

    # Create test user payload
    payload = {
        "sub": str(test_user.user_id),
        "username": test_user.username,
        "email": test_user.email,
        "roles": ["user"],
        "permissions": [],
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=24),  # Valid for 24 hours
        "type": "access"  # Required by auth middleware
    }

    # Generate token
    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    return token


@pytest.fixture
def invalid_jwt_token():
    """Generate an invalid JWT token for testing auth failures."""
    return "invalid.jwt.token"


@pytest.fixture
def expired_jwt_token(test_user):
    """Generate an expired JWT token for testing."""
    secret_key = os.getenv("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
    algorithm = "HS256"

    # Create expired token
    payload = {
        "sub": str(test_user.user_id),
        "username": test_user.username,
        "email": test_user.email,
        "roles": ["user"],
        "permissions": [],
        "iat": datetime.utcnow() - timedelta(hours=25),
        "exp": datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
    }

    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    return token


@pytest.fixture
def authenticated_client(app, test_jwt_token):
    """Create FastAPI test client with valid authentication headers."""
    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {test_jwt_token}"})
    return client


@pytest.fixture
def unauthenticated_client(app):
    """Create FastAPI test client without authentication headers."""
    return TestClient(app)


@pytest.fixture
def invalid_auth_client(app, invalid_jwt_token):
    """Create FastAPI test client with invalid authentication headers."""
    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {invalid_jwt_token}"})
    return client


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


# Data provisioning fixtures for lineup ownership tests
@pytest.fixture
def test_user_data(test_session):
    """Create test user data for lineup ownership tests."""
    import uuid
    from domains.users.models.user import User

    user_id = uuid.uuid4()
    user = User(
        user_id=user_id,
        username="testuser",
        email="testuser@example.com",
        cognito_sub=str(user_id),
        password_hash="$2b$12$test_hash_for_testing_purposes",  # Required field
        display_name="Test User",
        is_active=True,
    )
    test_session.add(user)
    test_session.commit()

    return {"user_id": user_id, "user": user}


@pytest.fixture
def test_league_data(test_session, test_user_data):
    """Create test league data for lineup ownership tests."""
    import uuid
    from domains.leagues.models.league import League

    league_id = uuid.uuid4()
    league = League(
        league_id=league_id,
        name="Test League",
        commissioner_id=test_user_data["user_id"],
        sport="nfl",
        league_type="head_to_head",  # Required field - must be 'head_to_head' or 'rotisserie'
        season="2024",  # Required field
        max_teams=10,
        status="active",
        invite_code="TEST123",  # Required field
    )
    test_session.add(league)
    test_session.commit()

    return {
        "league_id": league_id,
        "league": league,
        "commissioner_id": test_user_data["user_id"],
    }


@pytest.fixture
def test_team_data(test_session, test_user_data, test_league_data):
    """Create test team data for lineup ownership tests."""
    import uuid
    from domains.leagues.models.team import Team

    team_id = uuid.uuid4()
    team = Team(
        team_id=team_id,
        league_id=test_league_data["league_id"],
        user_id=test_user_data["user_id"],
        team_name="Test Team",
        waiver_priority=1,  # Use waiver_priority instead of draft_position
    )
    test_session.add(team)
    test_session.commit()

    return {
        "team_id": team_id,
        "team": team,
        "league_id": test_league_data["league_id"],
        "user_id": test_user_data["user_id"],
    }


@pytest.fixture
def test_lineup_data(test_session, test_team_data):
    """Create test lineup data for ownership tests."""
    import uuid
    from datetime import date
    from domains.lineups.models.lineup import Lineup

    lineup_id = uuid.uuid4()
    lineup = Lineup(
        lineup_id=lineup_id,
        team_id=test_team_data["team_id"],
        week=1,
        game_day=date.today(),
        players=[
            {"player_id": str(uuid.uuid4()), "position": "QB"},
            {"player_id": str(uuid.uuid4()), "position": "RB"},
        ],
        version=1,
        is_locked=False,
        points_scored=0.0,
    )
    test_session.add(lineup)
    test_session.commit()

    return {
        "lineup_id": lineup_id,
        "lineup": lineup,
        "team_id": test_team_data["team_id"],
        "user_id": test_team_data["user_id"],
    }


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
