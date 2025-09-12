from __future__ import annotations

"""
Integration Test — Scenario 1: Create and Join a League

Given a user is authenticated
When the user sends POST /leagues with a valid league configuration
Then a new league is created and the user is assigned as commissioner
And an invite link (or join capability) is returned
When another authenticated user posts to /leagues/{leagueId}/join
Then the user is added to the league as a manager

Notes:
- Auth is simulated via an "x-user-id" header (middleware to be implemented in T036).
- Database URL should be provided via DATABASE_URL. Tests may run against SQLite fallback in implementation,
  but here we only assert HTTP contract behavior; persistence details are validated by service/unit tests later.
"""

import uuid

from fastapi.testclient import TestClient


def test_create_and_join_league_flow(client: TestClient):
    user1 = str(uuid.uuid4())
    user2 = str(uuid.uuid4())

    # Create a new league
    create_payload = {
        "name": "Codex Premier League",
        "sport": "soccer",
        "league_type": "head_to_head",
        "season": "2025",
    }
    create_resp = client.post(
        "/leagues",
        json=create_payload,
        headers={"x-user-id": user1},
    )

    assert create_resp.status_code == 201
    league_data = create_resp.json()
    assert league_data["name"] == "Codex Premier League"
    assert league_data["sport"] == "soccer"
    assert league_data["league_type"] == "head_to_head"
    assert league_data["season"] == "2025"
    assert "league_id" in league_data
    assert "invite_link" in league_data

    league_id = league_data["league_id"]

    # Join the league with another user
    join_resp = client.post(
        f"/leagues/{league_id}/join",
        headers={"x-user-id": user2},
    )

    assert join_resp.status_code == 200
    join_data = join_resp.json()
    assert "team_id" in join_data
    assert join_data["league_id"] == league_id
    assert "team_name" in join_data
