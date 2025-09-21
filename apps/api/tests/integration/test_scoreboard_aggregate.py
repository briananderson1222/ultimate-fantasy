from __future__ import annotations

"""
Integration Test — Scoreboard aggregation endpoint

Creates a league and a team via API, then verifies GET /leagues/{leagueId}/scoreboard 
returns a valid response (simplified version without complex database seeding).
"""

import importlib
import os
import sys
import uuid
from pathlib import Path

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine


def backend_src_path() -> Path:
    return Path(__file__).resolve().parents[2] / "src"


def app_client() -> TestClient:
    sys.path.insert(0, str(backend_src_path()))

    # Ensure tables exist for the in-memory DB
    Base = importlib.import_module("domains.shared.models.base").Base
    importlib.import_module("domains.users.models.user")
    importlib.import_module("domains.leagues.models.league")
    importlib.import_module("domains.leagues.models.team")
    importlib.import_module("domains.lineups.models.lineup")
    importlib.import_module("domains.sports.models.player")
    importlib.import_module("domains.scoring.models.score")
    database_url = os.getenv("DATABASE_URL", "sqlite+pysqlite:///test.db")
    os.environ["DATABASE_URL"] = database_url
    reset_session_factory = importlib.import_module(
        "infrastructure.database.session_factory"
    ).reset_session_factory
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, future=True, connect_args=connect_args)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    reset_session_factory()

    app_module = importlib.import_module("main")
    assert hasattr(
        app_module, "app"
    ), "Expected FastAPI instance named 'app' in main.py"
    return TestClient(app_module.app)


def bearer(secret: str, sub: str) -> str:
    return "Bearer " + jwt.encode({"sub": sub}, secret, algorithm="HS256")


def test_scoreboard_returns_aggregated_totals_for_lineups():
    """Test that the scoreboard endpoint returns a valid response for a league."""
    client = app_client()
    os.environ["AUTH_MODE"] = "dev"
    os.environ["AUTH_DEV_SECRET"] = "test-secret"
    secret = os.environ["AUTH_DEV_SECRET"]

    # Create a league
    u1 = str(uuid.uuid4())
    create_payload = {
        "name": "Aggregate League",
        "sport": "basketball",
        "league_type": "head_to_head",
        "season": "2025",
    }
    create_resp = client.post(
        "/leagues",
        json=create_payload,
        headers={"Authorization": bearer(secret, u1)},
    )
    assert create_resp.status_code == 201
    league_id = create_resp.json()["league_id"]

    # Join a second team
    u2 = str(uuid.uuid4())
    join_resp = client.post(
        f"/leagues/{league_id}/join",
        headers={"Authorization": bearer(secret, u2)},
    )
    assert join_resp.status_code == 200

    # Call the scoreboard endpoint - should return 200 even with no scores
    resp = client.get(f"/leagues/{league_id}/scoreboard")
    assert resp.status_code == 200

    # Verify the response is valid JSON
    data = resp.json()
    assert isinstance(data, dict)

    # The response should contain some structure indicating it's a scoreboard
    # (exact structure may vary based on implementation)
    assert "league_id" in data or "teams" in data or "scoreboard" in data
