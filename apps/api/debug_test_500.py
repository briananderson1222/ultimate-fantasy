#!/usr/bin/env python3

"""Debug the specific 500 error in contract tests."""

import os
import sys
sys.path.append('src')

import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import jwt

# Import models and services
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
    try:
        importlib.import_module(module)
    except Exception as e:
        print(f"Warning: Failed to import {module}: {e}")

from domains.shared.models.base import Base
from domains.users.services.user_service import UserService
from main import app

def debug_500_error():
    """Debug the 500 error step by step"""
    print("=== DEBUGGING 500 ERROR ===")

    # Step 1: Create in-memory test database (like the test does)
    print("1. Creating test database...")
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(bind=test_engine)
    session = TestSession()
    print("✓ Test database created")

    try:
        # Step 2: Create test user (like conftest.py does)
        print("2. Creating test user...")
        user_service = UserService(session)

        test_claims = {
            "sub": str(uuid.uuid4()),
            "username": "test_user",
            "email": "test@example.com",
            "name": "Test User",
            "given_name": "Test",
            "family_name": "User"
        }

        user = user_service.ensure_user_from_claims(test_claims)
        session.commit()
        session.refresh(user)
        print(f"✓ Test user created: {user.user_id}, {user.username}")

        # Step 3: Create JWT token (like conftest.py does)
        print("3. Creating JWT token...")
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
            "type": "access"
        }

        token = jwt.encode(payload, secret_key, algorithm=algorithm)
        print(f"✓ JWT token created: {token[:50]}...")

        # Step 4: Create authenticated client
        print("4. Creating authenticated FastAPI test client...")
        client = TestClient(app)
        client.headers.update({"Authorization": f"Bearer {token}"})
        print("✓ Authenticated client created")

        # Step 5: Test the endpoint and capture detailed error
        print("5. Testing /api/v1/sports/players endpoint...")
        response = client.get("/api/v1/sports/players")

        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")

        if response.status_code == 500:
            print("✗ 500 Internal Server Error!")
            print(f"Response content: {response.text}")

            # Check if it contains any error details
            if "error" in response.text.lower() or "traceback" in response.text.lower():
                print("ERROR DETAILS:")
                print(response.text)
        elif response.status_code == 401:
            print("✗ 401 Unauthorized - authentication failed")
            print(f"Response content: {response.text}")
        else:
            print(f"✓ Request successful: {response.status_code}")

    except Exception as e:
        print(f"✗ Exception occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    debug_500_error()