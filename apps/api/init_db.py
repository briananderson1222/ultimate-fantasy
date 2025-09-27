#!/usr/bin/env python3

"""Manually initialize database."""

import os
import sys

sys.path.append("src")

# Import all required models to register metadata
import contextlib
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
    with contextlib.suppress(Exception):
        importlib.import_module(module)

from infrastructure.database.session_factory import get_session_factory

database_url = os.getenv("DATABASE_URL", "sqlite:///./ultimate_fantasy.db")

session_factory = get_session_factory()

# Initialize the session factory first
session_factory.initialize(database_url)

# Create tables
session_factory.create_tables_sync()
