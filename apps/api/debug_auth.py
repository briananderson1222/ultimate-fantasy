#!/usr/bin/env python3

"""Debug authentication token issues."""

import os
import sys
sys.path.append('src')

from fastapi.testclient import TestClient
from main import app
from domains.users.services.user_service import UserService
from infrastructure.database.session_factory import get_session_factory
import jwt
from datetime import datetime, timedelta
import uuid

# Create a test client
client = TestClient(app)

# First, create a user in the database
session_factory = get_session_factory()
db_session = session_factory.get_sync_session()

try:
    user_service = UserService(db_session)

    # Create user using the lazy-loaded method (ensure_user_from_claims)
    test_claims = {
        "sub": str(uuid.uuid4()),
        "username": "test_user",
        "email": "test@example.com",
        "name": "Test User"
    }

    user = user_service.ensure_user_from_claims(test_claims)
    print(f"Created user: {user.user_id}, {user.username}")

    payload = {
        "sub": str(user.user_id),  # Use the actual user ID
        "username": user.username,
        "email": user.email,
        "roles": ["user"],
        "permissions": [],
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=24),
        "type": "access"  # Required by auth middleware
    }

except Exception as e:
    print(f"Error creating user: {e}")
    payload = {
        "sub": str(uuid.uuid4()),
        "username": "test_user",
        "email": "test@example.com",
        "roles": ["user"],
        "permissions": [],
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=24),
        "type": "access"
    }
finally:
    db_session.close()

# Create JWT token using same logic as conftest.py but with the actual default
secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
algorithm = "HS256"
token = jwt.encode(payload, secret_key, algorithm=algorithm)
print(f"Generated token: {token}")

# Test the endpoint with auth header
headers = {"Authorization": f"Bearer {token}"}
response = client.get("/api/v1/sports/players", headers=headers)

print(f"Response status: {response.status_code}")
print(f"Response headers: {dict(response.headers)}")
print(f"Response content: {response.text}")

# Also test without auth
response_no_auth = client.get("/api/v1/sports/players")
print(f"\nWithout auth - Status: {response_no_auth.status_code}")
print(f"Without auth - Content: {response_no_auth.text}")