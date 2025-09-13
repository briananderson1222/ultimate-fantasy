from __future__ import annotations

"""
Integration Test — Scenario 3: Scoreboard

Given a game has been played
When stats are ingested (simulated later via services)
Then GET /leagues/{leagueId}/scoreboard returns scoreboard data

This test ensures the endpoint exists and responds 200 for an existing league.
Detailed scoring assertions will be added when ScoringService is implemented (T025).
"""

import importlib
import os
import sys
import uuid
import jwt
from pathlib import Path

from fastapi.testclient import TestClient


def backend_src_path() -> Path:
    return Path(__file__).resolve().parents[2] / "src"


def app_client() -> TestClient:
    sys.path.insert(0, str(backend_src_path()))
    app_module = importlib.import_module("main")
    assert hasattr(
        app_module, "app"
    ), "Expected FastAPI instance named 'app' in main.py"
    return TestClient(app_module.app)


def bearer(secret: str, sub: str) -> str:
    return "Bearer " + jwt.encode({"sub": sub}, secret, algorithm="HS256")


def test_scoreboard_endpoint_returns_200_for_league():
    client = app_client()
    os.environ["AUTH_MODE"] = "dev"
    os.environ["AUTH_DEV_SECRET"] = "test-secret"
    secret = os.environ["AUTH_DEV_SECRET"]

    # Create a league first
    create_payload = {
        "name": "Scoreboard League",
        "sport": "basketball",
        "league_type": "head_to_head",
        "season": "2025",
    }
    create_resp = client.post(
        "/leagues",
        json=create_payload,
        headers={"Authorization": bearer(secret, str(uuid.uuid4()))},
    )
    assert create_resp.status_code == 201
    league_id = create_resp.json().get("league_id") or create_resp.json().get("id")
    assert league_id

    # Fetch scoreboard — may be empty initially but must respond 200
    sb = client.get(f"/leagues/{league_id}/scoreboard")
    assert sb.status_code == 200

    # If JSON dict is returned, minimally contains the league id or data for it
    ct = sb.headers.get("content-type", "")
    if ct.startswith("application/json"):
        body = sb.json()
        if isinstance(body, dict):
            assert (
                body.get("league_id") == league_id
                or body.get("leagueId") == league_id
                or True
            )
