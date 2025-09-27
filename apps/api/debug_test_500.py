#!/usr/bin/env python3

"""Debug the specific 500 error in contract tests."""

import os
import sys

sys.path.append("src")

# Import models and services
import contextlib
import importlib
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

from domains.shared.models.base import Base
from domains.users.services.user_service import UserService
from main import app


def debug_500_error():
    """Debug the 500 error step by step"""
# print("=== DEBUGGING 500 ERROR ===")

    # Step 1: Create in-memory test database (like the test does)
# print("1. Creating test database...")
    test_engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(bind=test_engine)
    session = TestSession()
# print("✓ Test database created")

    try:
        # Step 2: Create test user (like conftest.py does)
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

        # Step 3: Create JWT token (like conftest.py does)
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

        # Step 4: Create authenticated client
        client = TestClient(app)
        client.headers.update({"Authorization": f"Bearer {token}"})

        # Step 5: Test the endpoint and capture detailed error
        response = client.get("/api/v1/sports/players")


        if response.status_code == 500:

            # Check if it contains any error details
            if "error" in response.text.lower() or "traceback" in response.text.lower():
                pass
        elif response.status_code == 401:
            pass
        else:
            pass

    except Exception:
        import traceback

        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    debug_500_error()
