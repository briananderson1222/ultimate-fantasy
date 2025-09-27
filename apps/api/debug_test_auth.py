#!/usr/bin/env python3

"""Debug the test authentication 500 errors step by step."""

import os
import sys

sys.path.append("src")

import builtins
import contextlib
import jwt

# Import test fixtures
from tests.conftest import (
    test_engine,
    test_session_factory,
    test_session,
    test_user,
    test_jwt_token,
    app,
    authenticated_client,
)


def debug_authentication_flow():
    """Debug each step of the authentication flow"""
# print("=== DEBUGGING AUTHENTICATION FLOW ===")

    # Step 1: Create test session
# print("1. Creating test database session...")
    test_db_url = "sqlite:///:memory:"
    test_engine_result = test_engine(test_db_url)
    test_session_factory_result = test_session_factory(test_engine_result)
    test_session_result = test_session(test_engine_result, test_session_factory_result)
# print(f"✓ Test session created: {type(test_session_result)}")

    # Step 2: Create test user
# print("2. Creating test user...")
    try:
        test_user_result = test_user(test_session_result)
    except Exception:
        import traceback

        traceback.print_exc()
        return

    # Step 3: Create JWT token
# print("3. Creating JWT token...")
    try:
        token = test_jwt_token(test_user_result)

        # Decode to verify
        secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
        jwt.decode(token, secret_key, algorithms=["HS256"])
    except Exception:
        import traceback

        traceback.print_exc()
        return

    # Step 4: Create authenticated client
# print("4. Creating authenticated client...")
    try:
        app_result = app()
        auth_client = authenticated_client(app_result, token)
    except Exception:
        import traceback

        traceback.print_exc()
        return

    # Step 5: Test the endpoint with detailed error tracking
# print("5. Testing endpoint...")
    try:
        response = auth_client.get("/api/v1/sports/players")

        if response.status_code != 200:

            # Try to parse error details
            with contextlib.suppress(builtins.BaseException):
                response.json()
        else:
            pass

    except Exception:
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_authentication_flow()
