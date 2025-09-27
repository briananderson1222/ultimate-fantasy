#!/usr/bin/env python3

"""Debug authentication step by step."""

import os
import sys
from contextlib import suppress

sys.path.append("src")

import logging
import uuid
from datetime import datetime, timedelta

import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from domains.users.services.user_service import UserService

# Create test database
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

# Import all required models to register metadata
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
    with suppress(Exception):
        importlib.import_module(module)
        # print(f"✓ Imported {module}")
        # print(f"✗ Failed to import {module}: {e}")

from domains.shared.models.base import Base

# Create all tables
Base.metadata.create_all(bind=engine)

# Create session
TestSession = sessionmaker(bind=engine)
session = TestSession()

try:
    # 1. Create a test user using the user service
    user_service = UserService(session)
    test_claims = {
        "sub": str(uuid.uuid4()),
        "username": "test_user",
        "email": "test@example.com",
        "name": "Test User",
        "given_name": "Test",
        "family_name": "User",
    }

# # print(f"Creating user with claims: {test_claims}")
    test_user = user_service.ensure_user_from_claims(test_claims)
# # print(f"✓ User created: {test_user.user_id}, {test_user.username}")

    # 2. Create JWT token
    secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
    algorithm = "HS256"

    payload = {
        "sub": str(test_user.user_id),
        "username": test_user.username,
        "email": test_user.email,
        "roles": ["user"],
        "permissions": [],
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=24),
        "type": "access",
    }

    token = jwt.encode(payload, secret_key, algorithm=algorithm)
# # print(f"✓ Token created: {token[:50]}...")

    # 3. Test user lookup
# # print(f"Looking up user by ID: {test_user.user_id!s}")
    found_user = user_service.get_user_sync(str(test_user.user_id))
# # print(f"✓ User found: {found_user.username}")

except Exception as e:
    logging.warning(f"Error: {e}")
    # # print(f"✗ Error: {e}")
    # import traceback

    # traceback.print_exc()

finally:
    session.close()
