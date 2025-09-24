#!/usr/bin/env python3

"""Debug the test authentication 500 errors step by step."""

import os
import sys
sys.path.append('src')

import tempfile
import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import jwt

# Import test fixtures
from tests.conftest import *

def debug_authentication_flow():
    """Debug each step of the authentication flow"""
    print("=== DEBUGGING AUTHENTICATION FLOW ===")

    # Step 1: Create test session
    print("1. Creating test database session...")
    test_db_url = "sqlite:///:memory:"
    test_engine_result = test_engine(test_db_url)
    test_session_factory_result = test_session_factory(test_engine_result)
    test_session_result = test_session(test_engine_result, test_session_factory_result)
    print(f"✓ Test session created: {type(test_session_result)}")

    # Step 2: Create test user
    print("2. Creating test user...")
    try:
        test_user_result = test_user(test_session_result)
        print(f"✓ Test user created: {test_user_result.user_id}, {test_user_result.username}")
        print(f"  User fields: id={test_user_result.user_id}, email={test_user_result.email}")
    except Exception as e:
        print(f"✗ Failed to create test user: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 3: Create JWT token
    print("3. Creating JWT token...")
    try:
        token = test_jwt_token(test_user_result)
        print(f"✓ JWT token created: {token[:50]}...")

        # Decode to verify
        secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
        decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
        print(f"  Token payload: {decoded}")
    except Exception as e:
        print(f"✗ Failed to create JWT token: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 4: Create authenticated client
    print("4. Creating authenticated client...")
    try:
        app_result = app()
        auth_client = authenticated_client(app_result, token)
        print(f"✓ Authenticated client created: {type(auth_client)}")
        print(f"  Client headers: {dict(auth_client.headers)}")
    except Exception as e:
        print(f"✗ Failed to create authenticated client: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 5: Test the endpoint with detailed error tracking
    print("5. Testing endpoint...")
    try:
        print("Making request to /api/v1/sports/players...")
        response = auth_client.get("/api/v1/sports/players")
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response content: {response.text[:500]}...")

        if response.status_code != 200:
            print(f"✗ Request failed with {response.status_code}")

            # Try to parse error details
            try:
                error_data = response.json()
                print(f"Error data: {error_data}")
            except:
                print("Could not parse error as JSON")
        else:
            print("✓ Request successful!")

    except Exception as e:
        print(f"✗ Request failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_authentication_flow()