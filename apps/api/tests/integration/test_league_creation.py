"""
League Creation Integration Test - T009

Tests complete league experience from quickstart scenario 1:
User registration → league creation → team joining → setup validation

This test MUST FAIL initially to follow TDD principles.
"""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
import json

# Import will fail initially - this is expected for TDD
try:
    from src.main import app
    client = TestClient(app)
except ImportError:
    client = None


class TestLeagueCreationFlow:
    """Integration test for complete league creation workflow"""

    def test_complete_league_experience_scenario_1(self):
        """Test the complete league experience from quickstart scenario 1"""
        if not client:
            pytest.fail("Application not implemented yet - TDD failing test")

        # Step 1: User registration
        commissioner_data = {
            "email": "commissioner@test.com",
            "password": "password123",
            "name": "Test Commissioner"
        }

        register_response = client.post("/api/v1/auth/register", json=commissioner_data)
        assert register_response.status_code == 201

        commissioner_user = register_response.json()
        assert "user_id" in commissioner_user
        assert "access_token" in commissioner_user

        commissioner_token = commissioner_user["access_token"]
        commissioner_headers = {"Authorization": f"Bearer {commissioner_token}"}

        # Step 2: Create MLB league
        league_data = {
            "name": "Test MLB League",
            "sport": "mlb",
            "league_type": "head_to_head",
            "season": "2025",
            "max_teams": 8,
            "scoring_rules": {"hits": 1, "home_runs": 4, "rbis": 1},
            "draft_settings": {"type": "snake", "pick_timer": 60}
        }

        league_response = client.post(
            "/api/v1/leagues",
            json=league_data,
            headers=commissioner_headers
        )
        assert league_response.status_code == 201

        league = league_response.json()
        assert "league_id" in league
        assert "invite_code" in league
        assert league["name"] == "Test MLB League"
        assert league["sport"] == "mlb"
        assert league["status"] == "setup"

        league_id = league["league_id"]
        invite_code = league["invite_code"]

        # Verify commissioner team was automatically created
        teams_response = client.get(
            f"/api/v1/leagues/{league_id}/teams",
            headers=commissioner_headers
        )
        assert teams_response.status_code == 200

        teams = teams_response.json()
        assert len(teams) == 1
        assert teams[0]["user_id"] == commissioner_user["user_id"]

        # Step 3: Second user registration
        user2_data = {
            "email": "user2@test.com",
            "password": "password123",
            "name": "Test User 2"
        }

        user2_register_response = client.post("/api/v1/auth/register", json=user2_data)
        assert user2_register_response.status_code == 201

        user2 = user2_register_response.json()
        user2_token = user2["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        # Step 4: Join league with invite code
        join_data = {
            "team_name": "Test Team 2",
            "invite_code": invite_code
        }

        join_response = client.post(
            f"/api/v1/leagues/{league_id}/join",
            json=join_data,
            headers=user2_headers
        )
        assert join_response.status_code == 201

        team2 = join_response.json()
        assert "team_id" in team2
        assert team2["team_name"] == "Test Team 2"
        assert team2["league_id"] == league_id

        # Step 5: Validate final state
        # League should now have 2 teams
        final_teams_response = client.get(
            f"/api/v1/leagues/{league_id}/teams",
            headers=commissioner_headers
        )
        assert final_teams_response.status_code == 200

        final_teams = final_teams_response.json()
        assert len(final_teams) == 2

        # League should still be in setup status
        league_status_response = client.get(
            f"/api/v1/leagues/{league_id}",
            headers=commissioner_headers
        )
        assert league_status_response.status_code == 200

        final_league = league_status_response.json()
        assert final_league["status"] == "setup"
        assert len(final_league["teams"]) == 2

    def test_league_creation_validation(self):
        """Test league creation validation rules"""
        if not client:
            pytest.fail("Application not implemented yet - TDD failing test")

        # Create a user first
        user_data = {
            "email": "test@test.com",
            "password": "password123",
            "name": "Test User"
        }

        register_response = client.post("/api/v1/auth/register", json=user_data)
        user_token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {user_token}"}

        # Test invalid sport
        invalid_league_data = {
            "name": "Invalid League",
            "sport": "invalid_sport",
            "league_type": "head_to_head",
            "season": "2025",
            "max_teams": 8
        }

        response = client.post("/api/v1/leagues", json=invalid_league_data, headers=headers)
        assert response.status_code == 400

        # Test invalid max_teams (too low)
        invalid_teams_data = {
            "name": "Invalid Teams League",
            "sport": "mlb",
            "league_type": "head_to_head",
            "season": "2025",
            "max_teams": 1
        }

        response = client.post("/api/v1/leagues", json=invalid_teams_data, headers=headers)
        assert response.status_code == 400

        # Test invalid max_teams (too high)
        invalid_teams_data["max_teams"] = 25
        response = client.post("/api/v1/leagues", json=invalid_teams_data, headers=headers)
        assert response.status_code == 400

    def test_duplicate_team_names_in_league(self):
        """Test that duplicate team names are not allowed in the same league"""
        if not client:
            pytest.fail("Application not implemented yet - TDD failing test")

        # Create league with first user
        user1_data = {"email": "user1@test.com", "password": "password123", "name": "User 1"}
        user1_response = client.post("/api/v1/auth/register", json=user1_data)
        user1_token = user1_response.json()["access_token"]
        user1_headers = {"Authorization": f"Bearer {user1_token}"}

        league_data = {
            "name": "Test League",
            "sport": "mlb",
            "league_type": "head_to_head",
            "season": "2025",
            "max_teams": 8
        }

        league_response = client.post("/api/v1/leagues", json=league_data, headers=user1_headers)
        league = league_response.json()
        league_id = league["league_id"]
        invite_code = league["invite_code"]

        # Second user tries to join with same team name as commissioner
        user2_data = {"email": "user2@test.com", "password": "password123", "name": "User 2"}
        user2_response = client.post("/api/v1/auth/register", json=user2_data)
        user2_token = user2_response.json()["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        # Get commissioner's team name
        teams_response = client.get(f"/api/v1/leagues/{league_id}/teams", headers=user1_headers)
        commissioner_team_name = teams_response.json()[0]["name"]

        join_data = {
            "team_name": commissioner_team_name,  # Same name as commissioner
            "invite_code": invite_code
        }

        join_response = client.post(
            f"/api/v1/leagues/{league_id}/join",
            json=join_data,
            headers=user2_headers
        )
        assert join_response.status_code == 400

        error = join_response.json()
        assert "team name" in error["detail"].lower()

    def test_league_capacity_limits(self):
        """Test that leagues enforce max_teams capacity"""
        if not client:
            pytest.fail("Application not implemented yet - TDD failing test")

        # Create league with max_teams = 2
        commissioner_data = {"email": "commissioner@test.com", "password": "password123", "name": "Commissioner"}
        commissioner_response = client.post("/api/v1/auth/register", json=commissioner_data)
        commissioner_token = commissioner_response.json()["access_token"]
        commissioner_headers = {"Authorization": f"Bearer {commissioner_token}"}

        league_data = {
            "name": "Small League",
            "sport": "mlb",
            "league_type": "head_to_head",
            "season": "2025",
            "max_teams": 2  # Only 2 teams allowed
        }

        league_response = client.post("/api/v1/leagues", json=league_data, headers=commissioner_headers)
        league = league_response.json()
        league_id = league["league_id"]
        invite_code = league["invite_code"]

        # First user joins successfully
        user1_data = {"email": "user1@test.com", "password": "password123", "name": "User 1"}
        user1_response = client.post("/api/v1/auth/register", json=user1_data)
        user1_token = user1_response.json()["access_token"]
        user1_headers = {"Authorization": f"Bearer {user1_token}"}

        join1_data = {"team_name": "Team 1", "invite_code": invite_code}
        join1_response = client.post(f"/api/v1/leagues/{league_id}/join", json=join1_data, headers=user1_headers)
        assert join1_response.status_code == 201

        # Second user tries to join but league is full
        user2_data = {"email": "user2@test.com", "password": "password123", "name": "User 2"}
        user2_response = client.post("/api/v1/auth/register", json=user2_data)
        user2_token = user2_response.json()["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        join2_data = {"team_name": "Team 2", "invite_code": invite_code}
        join2_response = client.post(f"/api/v1/leagues/{league_id}/join", json=join2_data, headers=user2_headers)
        assert join2_response.status_code == 400

        error = join2_response.json()
        assert "full" in error["detail"].lower() or "capacity" in error["detail"].lower()

    def test_invalid_invite_code(self):
        """Test that invalid invite codes are rejected"""
        if not client:
            pytest.fail("Application not implemented yet - TDD failing test")

        # Register user
        user_data = {"email": "user@test.com", "password": "password123", "name": "User"}
        user_response = client.post("/api/v1/auth/register", json=user_data)
        user_token = user_response.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # Try to join with invalid invite code
        join_data = {
            "team_name": "Test Team",
            "invite_code": "INVALID123"
        }

        # This should fail because no league has this invite code
        join_response = client.post(
            f"/api/v1/leagues/{str(uuid4())}/join",
            json=join_data,
            headers=user_headers
        )
        assert join_response.status_code == 404