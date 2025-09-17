from __future__ import annotations

import importlib
import os
import sys
import uuid
from datetime import date
from pathlib import Path

import jwt
from fastapi.testclient import TestClient


def backend_src_path() -> Path:
    return Path(__file__).resolve().parents[2] / "src"


def app_client() -> TestClient:
    sys.path.insert(0, str(backend_src_path()))
    os.environ["AUTH_MODE"] = "dev"
    os.environ["AUTH_DEV_SECRET"] = "test-secret"

    # Ensure tables exist for in-memory sqlite
    Base = importlib.import_module("models.base").Base
    get_engine = importlib.import_module("services.db").get_engine
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    app_module = importlib.import_module("main")
    return TestClient(app_module.app)


def bearer(sub: str) -> dict[str, str]:
    secret = os.environ.get("AUTH_DEV_SECRET", "test-secret")
    token = jwt.encode({"sub": sub}, secret, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


def create_league(client: TestClient, user_sub: str) -> str:
    payload = {
        "name": "UI League",
        "sport": "basketball",
        "league_type": "head_to_head",
        "season": "2025",
    }
    r = client.post("/leagues", json=payload, headers=bearer(user_sub))
    assert r.status_code == 201
    return r.json()["league_id"]


def test_me_leagues_lists_memberships():
    client = app_client()
    user1, user2 = str(uuid.uuid4()), str(uuid.uuid4())
    league_id = create_league(client, user1)
    # user2 joins
    rj = client.post(f"/leagues/{league_id}/join", headers=bearer(user2))
    assert rj.status_code == 200

    # Query /me/leagues as user2 — should include the created league
    r = client.get("/me/leagues", headers=bearer(user2))
    assert r.status_code == 200
    body = r.json()
    assert any(it.get("league_id") == league_id for it in body.get("items", []))


def test_league_members_lists_commissioner_and_joined_users():
    client = app_client()
    user1, user2 = str(uuid.uuid4()), str(uuid.uuid4())
    league_id = create_league(client, user1)
    rj = client.post(f"/leagues/{league_id}/join", headers=bearer(user2))
    assert rj.status_code == 200

    r = client.get(f"/leagues/{league_id}/members")
    assert r.status_code == 200
    items = r.json().get("items", [])
    assert len(items) >= 2
    user_ids = {it.get("user_id") for it in items}
    assert user1 in user_ids and user2 in user_ids


def test_waivers_list_filters_by_league_and_team():
    client = app_client()
    user = str(uuid.uuid4())
    league_id = create_league(client, user)
    # Place two bids for two different teams
    team_a = str(uuid.uuid4())
    team_b = str(uuid.uuid4())
    # We don't have create-team endpoint; place bids using existing API, ids are arbitrary for sqlite
    bid_a = {
        "league_id": league_id,
        "team_id": team_a,
        "player_id": str(uuid.uuid4()),
        "bid": 5,
    }
    bid_b = {
        "league_id": league_id,
        "team_id": team_b,
        "player_id": str(uuid.uuid4()),
        "bid": 7,
    }
    client.post("/waivers/bids", json=bid_a, headers=bearer(user))
    client.post("/waivers/bids", json=bid_b, headers=bearer(user))

    # List by league only
    r_all = client.get(f"/waivers?league_id={league_id}")
    assert r_all.status_code == 200
    assert len(r_all.json().get("items", [])) >= 2

    # Filter by team
    r_team = client.get(f"/waivers?league_id={league_id}&team_id={team_a}")
    assert r_team.status_code == 200
    items = r_team.json().get("items", [])
    assert all(it.get("team_id") == team_a for it in items)


def test_lineups_list_by_team_and_day():
    client = app_client()
    user = str(uuid.uuid4())
    # We will use arbitrary team_id for sqlite; create league to ensure DB exists
    create_league(client, user)

    team_id = str(uuid.uuid4())
    day1 = date(2025, 1, 1)
    day2 = date(2025, 1, 2)
    # Create two lineups
    client.put(
        "/lineups",
        json={
            "team_id": team_id,
            "game_day": day1.isoformat(),
            "players": [{"player_id": str(uuid.uuid4()), "position": "G"}],
        },
        headers=bearer(user),
    )
    client.put(
        "/lineups",
        json={
            "team_id": team_id,
            "game_day": day2.isoformat(),
            "players": [{"player_id": str(uuid.uuid4()), "position": "F"}],
        },
        headers=bearer(user),
    )

    # List all for team
    r_all = client.get(f"/lineups?team_id={team_id}")
    assert r_all.status_code == 200
    assert len(r_all.json().get("items", [])) >= 2

    # Filter by day
    r_day = client.get(f"/lineups?team_id={team_id}&game_day={day1.isoformat()}")
    assert r_day.status_code == 200
    items = r_day.json().get("items", [])
    assert all(it.get("game_day") == day1.isoformat() for it in items)
