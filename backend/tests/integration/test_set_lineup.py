from __future__ import annotations

"""
Integration Test — Scenario 2: Set a Lineup

Given a manager is in a league
When the manager sends PUT /lineups with a valid lineup for the current game day
Then the lineup is saved and validated against the league's rules

Notes:
- Auth uses Authorization: Bearer (dev HS256 token in tests).
- Minimal assertion is HTTP 200 as per contract; response body shape is validated if JSON is returned.
"""

import importlib
import os
import sys
import uuid
import jwt
from datetime import date
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


def test_set_lineup_accepts_valid_payload():
    client = app_client()
    os.environ["AUTH_MODE"] = "dev"
    os.environ["AUTH_DEV_SECRET"] = "test-secret"
    secret = os.environ["AUTH_DEV_SECRET"]

    payload = {
        "team_id": str(uuid.uuid4()),
        "game_day": date.today().isoformat(),
        "players": [
            {"player_id": str(uuid.uuid4()), "position": "FLEX"},
            {"player_id": str(uuid.uuid4()), "position": "FLEX"},
        ],
    }

    resp = client.put(
        "/lineups",
        json=payload,
        headers={"Authorization": bearer(secret, str(uuid.uuid4()))},
    )
    assert resp.status_code == 200

    # If server returns the saved lineup, validate minimal shape
    if resp.headers.get("content-type", "").startswith("application/json"):
        body = resp.json()
        assert (
            body.get("team_id") == payload["team_id"]
            or body.get("teamId") == payload["team_id"]
        )
        assert (
            body.get("game_day") == payload["game_day"]
            or body.get("gameDay") == payload["game_day"]
        )
