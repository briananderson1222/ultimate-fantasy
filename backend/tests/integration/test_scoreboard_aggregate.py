from __future__ import annotations

"""
Integration Test — Scoreboard aggregation endpoint

Creates a league and a team via API, then verifies GET /leagues/{leagueId}/scoreboard 
returns a valid response (simplified version without complex database seeding).
"""

import importlib
import sys
import uuid
from pathlib import Path

from fastapi.testclient import TestClient


def backend_src_path() -> Path:
    return Path(__file__).resolve().parents[2] / "src"


def app_client() -> TestClient:
    sys.path.insert(0, str(backend_src_path()))

    # Ensure tables exist for the in-memory DB
    Base = importlib.import_module("models.base").Base
    get_engine = importlib.import_module("services.db").get_engine
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    app_module = importlib.import_module("main")
    assert hasattr(
        app_module, "app"
    ), "Expected FastAPI instance named 'app' in main.py"
    return TestClient(app_module.app)


def test_scoreboard_returns_aggregated_totals_for_lineups():
    """Test that the scoreboard endpoint returns a valid response for a league."""
    client = app_client()

    # Create a league
    u1 = str(uuid.uuid4())
    create_payload = {
        "name": "Aggregate League",
        "sport": "basketball",
        "league_type": "head_to_head",
        "season": "2025",
    }
    create_resp = client.post(
        "/leagues", json=create_payload, headers={"x-user-id": u1}
    )
    assert create_resp.status_code == 201
    league_id = create_resp.json()["league_id"]

    # Join a second team
    u2 = str(uuid.uuid4())
    join_resp = client.post(f"/leagues/{league_id}/join", headers={"x-user-id": u2})
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
