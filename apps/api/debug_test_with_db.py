#!/usr/bin/env python3

"""Debug authentication with proper test database configuration."""

import os
import sys

sys.path.append("src")

# Import models and services
import contextlib
import importlib
import tempfile
import uuid
from datetime import datetime, timedelta

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
    with contextlib.suppress(Exception):
        importlib.import_module(module)

import builtins
import contextlib

from domains.shared.models.base import Base
from domains.users.services.user_service import UserService


def test_with_shared_database():
    """Test with a file-based database that both test and app can access"""
# print("=== TESTING WITH SHARED DATABASE ===")

    # Create a temporary database file that both test and app can access
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        test_db_path = tmp_db.name

# print(f"Using temporary database: {test_db_path}")

    # Set the DATABASE_URL environment variable for the app
    os.environ["DATABASE_URL"] = f"sqlite:///{test_db_path}"

    try:
        # Step 1: Create and setup the database with proper schema
        test_engine = create_engine(
            f"sqlite:///{test_db_path}", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=test_engine)
        TestSession = sessionmaker(bind=test_engine)
        session = TestSession()

        # Step 2: Create test user
        user_service = UserService(session)

        test_claims = {
            "sub": str(uuid.uuid4()),
            "username": "test_user",
            "email": "test@example.com",
            "name": "Test User",
            "given_name": "Test",
            "family_name": "User",
        }

        user = user_service.ensure_user_from_claims(test_claims)
        session.commit()
        session.refresh(user)

        # Verify user exists in database
        from domains.users.models.user import User

        session.query(User).filter(User.user_id == user.user_id).first()

        # Step 3: Create JWT token
        secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
        algorithm = "HS256"

        payload = {
            "sub": str(user.user_id),
            "username": user.username,
            "email": user.email,
            "roles": ["user"],
            "permissions": [],
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=24),
            "type": "access",
        }

        token = jwt.encode(payload, secret_key, algorithm=algorithm)

        # Close the session before starting the app
        session.close()

        # Step 4: Import and create the app AFTER setting environment variable

        # Clear any cached modules that might have old database connections
        if "main" in sys.modules:
            del sys.modules["main"]
        if "infrastructure.container" in sys.modules:
            del sys.modules["infrastructure.container"]

        from main import app

        client = TestClient(app)
        client.headers.update({"Authorization": f"Bearer {token}"})

        # Step 5: Test the endpoint
        response = client.get("/api/v1/sports/players")


        if response.status_code == 200:
            response.json()
        elif response.status_code in {500, 401}:
            pass
        else:
            pass

    except Exception:
        import traceback

        traceback.print_exc()
    finally:
        # Clean up
        with contextlib.suppress(builtins.BaseException):
            os.unlink(test_db_path)


if __name__ == "__main__":
    test_with_shared_database()
