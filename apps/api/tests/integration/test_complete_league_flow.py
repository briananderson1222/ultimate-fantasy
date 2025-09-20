"""
Integration test for complete league experience workflow.

Tests the full user journey from quickstart scenario 1:
User registration → league creation → team joining → setup validation

This test must fail before implementation (TDD approach).
"""

import pytest
from fastapi.testclient import TestClient

from main import app


class TestCompleteLeagueFlow:
    """Integration tests for complete league creation and joining flow."""

    def setup_method(self):
        """Set up test client and test data."""
        self.client = TestClient(app)

        # Test data for the complete flow
        self.user1_data = {
            "username": "commissioner_user",
            "email": "commissioner@example.com",
            "password": "secure_password123"
        }

        self.user2_data = {
            "username": "league_member",
            "email": "member@example.com",
            "password": "secure_password456"
        }

        self.league_data = {
            "name": "Test Fantasy League",
            "sport": "NFL",
            "max_teams": 10,
            "scoring_type": "standard",
            "draft_type": "snake",
            "draft_date": "2024-09-01T10:00:00Z"
        }

    def test_complete_league_creation_and_joining_flow(self):
        """
        Integration Test: Complete league experience end-to-end.

        This test will FAIL until all components are implemented:
        1. User registration
        2. League creation
        3. Team joining
        4. Setup validation
        """

        # Step 1: Register commissioner user
        register_response = self.client.post("/api/v1/auth/register", json=self.user1_data)
        assert register_response.status_code == 201
        commissioner_data = register_response.json()
        assert "access_token" in commissioner_data

        commissioner_token = commissioner_data["access_token"]
        commissioner_headers = {"Authorization": f"Bearer {commissioner_token}"}

        # Step 2: Create league as commissioner
        league_response = self.client.post(
            "/api/v1/leagues",
            json=self.league_data,
            headers=commissioner_headers
        )
        assert league_response.status_code == 201
        league_data = league_response.json()
        assert "league_id" in league_data
        assert "invite_code" in league_data

        league_id = league_data["league_id"]
        invite_code = league_data["invite_code"]

        # Step 3: Register second user
        register_response_2 = self.client.post("/api/v1/auth/register", json=self.user2_data)
        assert register_response_2.status_code == 201
        member_data = register_response_2.json()

        member_token = member_data["access_token"]
        member_headers = {"Authorization": f"Bearer {member_token}"}

        # Step 4: Join league using invite code
        join_data = {
            "invite_code": invite_code,
            "team_name": "My Fantasy Team"
        }
        join_response = self.client.post(
            f"/api/v1/leagues/{league_id}/join",
            json=join_data,
            headers=member_headers
        )
        assert join_response.status_code == 200
        join_result = join_response.json()
        assert "team_id" in join_result

        # Step 5: Validate league setup
        league_status_response = self.client.get(
            f"/api/v1/leagues/{league_id}",
            headers=commissioner_headers
        )
        assert league_status_response.status_code == 200
        league_status = league_status_response.json()

        assert league_status["team_count"] == 2
        assert len(league_status["teams"]) == 2
        assert league_status["status"] == "setup"

        # Step 6: Get teams in league
        teams = league_status["teams"]
        commissioner_team = next(team for team in teams if team["is_commissioner"])
        member_team = next(team for team in teams if not team["is_commissioner"])

        assert commissioner_team["owner"] == self.user1_data["username"]
        assert member_team["owner"] == self.user2_data["username"]
        assert member_team["name"] == "My Fantasy Team"

    def test_league_creation_requires_authentication(self):
        """
        Integration Test: League creation requires valid authentication.

        This test will FAIL until authentication is implemented.
        """
        response = self.client.post("/api/v1/leagues", json=self.league_data)
        assert response.status_code == 401

    def test_league_joining_with_invalid_invite_code_fails(self):
        """
        Integration Test: League joining with invalid invite code fails.

        This test will FAIL until validation is implemented.
        """
        # Register user first
        register_response = self.client.post("/api/v1/auth/register", json=self.user2_data)
        assert register_response.status_code == 201
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try to join with invalid invite code
        join_data = {
            "invite_code": "INVALID_CODE",
            "team_name": "My Team"
        }
        response = self.client.post(
            "/api/v1/leagues/some_league_id/join",
            json=join_data,
            headers=headers
        )
        assert response.status_code == 400

    def test_league_member_limit_enforcement(self):
        """
        Integration Test: League enforces maximum team limit.

        This test will FAIL until capacity validation is implemented.
        """
        # Create league with max_teams = 1
        small_league_data = {**self.league_data, "max_teams": 1}

        # Register commissioner
        register_response = self.client.post("/api/v1/auth/register", json=self.user1_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create league
        league_response = self.client.post("/api/v1/leagues", json=small_league_data, headers=headers)
        league_id = league_response.json()["league_id"]
        invite_code = league_response.json()["invite_code"]

        # Register second user
        register_response_2 = self.client.post("/api/v1/auth/register", json=self.user2_data)
        member_token = register_response_2.json()["access_token"]
        member_headers = {"Authorization": f"Bearer {member_token}"}

        # Try to join full league
        join_data = {"invite_code": invite_code, "team_name": "Second Team"}
        response = self.client.post(
            f"/api/v1/leagues/{league_id}/join",
            json=join_data,
            headers=member_headers
        )
        assert response.status_code == 400
        assert "full" in response.json()["message"].lower()

    def test_duplicate_team_names_in_league_rejected(self):
        """
        Integration Test: Duplicate team names in same league are rejected.

        This test will FAIL until uniqueness validation is implemented.
        """
        # Set up league with commissioner
        register_response = self.client.post("/api/v1/auth/register", json=self.user1_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        league_response = self.client.post("/api/v1/leagues", json=self.league_data, headers=headers)
        league_id = league_response.json()["league_id"]
        invite_code = league_response.json()["invite_code"]

        # First member joins with team name
        register_response_2 = self.client.post("/api/v1/auth/register", json=self.user2_data)
        member_token = register_response_2.json()["access_token"]
        member_headers = {"Authorization": f"Bearer {member_token}"}

        join_data = {"invite_code": invite_code, "team_name": "Duplicate Name"}
        first_join = self.client.post(
            f"/api/v1/leagues/{league_id}/join",
            json=join_data,
            headers=member_headers
        )
        assert first_join.status_code == 200

        # Second member tries same team name
        user3_data = {**self.user2_data, "username": "user3", "email": "user3@example.com"}
        register_response_3 = self.client.post("/api/v1/auth/register", json=user3_data)
        member3_token = register_response_3.json()["access_token"]
        member3_headers = {"Authorization": f"Bearer {member3_token}"}

        duplicate_join = self.client.post(
            f"/api/v1/leagues/{league_id}/join",
            json=join_data,  # Same team name
            headers=member3_headers
        )
        assert duplicate_join.status_code == 400
        assert "team name already exists" in duplicate_join.json()["message"].lower()