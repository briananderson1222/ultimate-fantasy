from __future__ import annotations

"""
Integration Test — Scenario 4: Waiver Claim

Given a player is on waivers
When a manager places a bid by POST /waivers/bids
Then the bid is recorded (201)

Notes:
- Auth uses Authorization: Bearer (dev HS256 token in tests).
- Resolution of waivers (awarding the player) happens after the period ends and
  is handled by WaiverService (T026). This test focuses on the HTTP contract for placing bids.
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


def create_league(client: TestClient, secret: str) -> str:
    payload = {
        "name": "Waiver League",
        "sport": "baseball",
        "league_type": "head_to_head",
        "season": "2025",
    }
    resp = client.post(
        "/leagues",
        json=payload,
        headers={"Authorization": bearer(secret, str(uuid.uuid4()))},
    )
    assert resp.status_code == 201
    body = resp.json()
    return body.get("league_id") or body.get("id")


def test_place_waiver_bid_returns_201():
    client = app_client()
    os.environ["AUTH_MODE"] = "dev"
    os.environ["AUTH_DEV_SECRET"] = "test-secret"
    secret = os.environ["AUTH_DEV_SECRET"]

    league_id = create_league(client, secret)
    team_id = str(uuid.uuid4())
    player_id = str(uuid.uuid4())

    bid_payload = {
        "league_id": league_id,
        "team_id": team_id,
        "player_id": player_id,
        "bid": 42,
    }

    resp = client.post(
        "/waivers/bids",
        json=bid_payload,
        headers={"Authorization": bearer(secret, str(uuid.uuid4()))},
    )
    assert resp.status_code == 201

    # If JSON is returned, minimally verify fields are echoed or an id is provided
    if resp.headers.get("content-type", "").startswith("application/json"):
        data = resp.json()
        assert (
            data.get("league_id") == league_id
            or data.get("leagueId") == league_id
            or data.get("waiver_id")
        )
