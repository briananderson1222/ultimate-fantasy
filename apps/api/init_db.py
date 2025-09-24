#!/usr/bin/env python3

"""Manually initialize database."""

import os
import sys
sys.path.append('src')

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

print("Importing models...")
for module in required_models:
    try:
        importlib.import_module(module)
        print(f"✓ Imported {module}")
    except Exception as e:
        print(f"✗ Failed to import {module}: {e}")

from domains.shared.models.base import Base
from infrastructure.database.session_factory import get_session_factory

print("\nInitializing database...")
database_url = os.getenv("DATABASE_URL", "sqlite:///./ultimate_fantasy.db")
print(f"Database URL: {database_url}")

session_factory = get_session_factory()
print("Got session factory")

# Initialize the session factory first
session_factory.initialize(database_url)
print("Session factory initialized")

# Create tables
print("Creating tables...")
session_factory.create_tables_sync()
print("✓ Database tables created successfully!")