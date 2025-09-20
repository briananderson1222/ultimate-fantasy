"""
Waiver System Integration Test - T012

Tests waiver workflow from quickstart scenario 2:
Bid placement → processing → player assignment

This test MUST FAIL initially to follow TDD principles.
"""

import pytest
from fastapi.testclient import TestClient

try:
    from src.main import app
    client = TestClient(app)
except ImportError:
    client = None


class TestWaiverSystemFlow:
    """Integration test for complete waiver system workflow"""

    def test_complete_waiver_workflow_scenario_2(self):
        """Test the complete waiver workflow from quickstart scenario 2"""
        if not client:
            pytest.fail("Application not implemented yet - TDD failing test")

        # Setup league and get available players
        league_id, team_headers, team_data = self._setup_league_with_team()

        # Step 1: Place waiver bid
        available_players = client.get("/api/v1/sports/players?sport=mlb").json()
        free_agent_id = available_players[0]["player_id"]
        bench_player_id = team_data["roster"][0] if team_data["roster"] else None

        bid_data = {
            "league_id": league_id,
            "team_id": team_data["team_id"],
            "player_id": free_agent_id,
            "bid_amount": 25,
            "drop_player_id": bench_player_id
        }

        bid_response = client.post("/api/v1/waivers/bids", json=bid_data, headers=team_headers)
        assert bid_response.status_code == 201

        bid = bid_response.json()
        assert bid["status"] == "pending"
        assert bid["bid_amount"] == 25

        # Step 2: Process waivers (admin action)
        admin_headers = self._get_admin_headers()
        process_response = client.post(
            "/api/v1/admin/waivers/process",
            json={"league_id": league_id},
            headers=admin_headers
        )
        assert process_response.status_code == 200

        # Step 3: Verify results
        results = process_response.json()
        assert "processed_bids" in results
        assert len(results["processed_bids"]) >= 1

        # Check if bid was won (highest bid should win)
        processed_bid = results["processed_bids"][0]
        assert processed_bid["status"] in ["won", "lost"]

    def _setup_league_with_team(self):
        """Helper to set up league with a team"""
        # Create user and league
        user_data = {"email": "waiver@test.com", "password": "password123", "name": "Waiver Test"}
        user_response = client.post("/api/v1/auth/register", json=user_data)
        token = user_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        league_data = {"name": "Waiver League", "sport": "mlb", "max_teams": 8}
        league_response = client.post("/api/v1/leagues", json=league_data, headers=headers)
        league_id = league_response.json()["league_id"]

        # Get team data
        teams_response = client.get(f"/api/v1/leagues/{league_id}/teams", headers=headers)
        team_data = teams_response.json()[0]

        return league_id, headers, team_data

    def _get_admin_headers(self):
        """Helper to get admin authorization"""
        # In a real implementation, this would authenticate as admin
        admin_data = {"email": "admin@test.com", "password": "admin123", "role": "admin"}
        admin_response = client.post("/api/v1/auth/admin-login", json=admin_data)
        token = admin_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}