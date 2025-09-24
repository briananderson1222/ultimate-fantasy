"""
Draft Process Integration Test - T010

Tests draft workflow from quickstart scenario 1:
Draft start → pick selection → snake order → completion

This test MUST FAIL initially to follow TDD principles.
"""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
import json
import time

# Import will fail initially - this is expected for TDD
try:
    from src.main import app

    client = TestClient(app)
except ImportError:
    client = None


class TestDraftProcessFlow:
    """Integration test for complete draft process workflow"""

    def test_complete_draft_workflow_scenario_1(self):
        """Test the complete draft workflow from quickstart scenario 1"""
        if not client:
            pytest.fail("Application not implemented yet - TDD failing test")

        # Setup: Create league with 2 teams
        league_id, commissioner_headers, user2_headers = self._setup_league_with_teams()

        # Step 1: Start draft (commissioner only)
        draft_data = {"draft_type": "snake", "pick_timer": 60}

        draft_response = client.post(
            f"/api/v1/draft/{league_id}", json=draft_data, headers=commissioner_headers
        )
        assert draft_response.status_code == 201

        draft = draft_response.json()
        assert "draft_id" in draft
        assert draft["status"] == "active"
        assert draft["draft_type"] == "snake"
        assert draft["pick_timer"] == 60

        # Verify draft status changed
        draft_status_response = client.get(
            f"/api/v1/draft/{league_id}", headers=commissioner_headers
        )
        assert draft_status_response.status_code == 200

        draft_status = draft_status_response.json()
        assert draft_status["status"] == "active"
        assert draft_status["current_pick"] == 1

        # Step 2: Make first pick (commissioner's turn)
        # Get available players first
        players_response = client.get("/api/v1/sports/players?sport=mlb")
        assert players_response.status_code == 200

        players = players_response.json()
        assert len(players) > 0

        mike_trout_id = self._find_player_by_name(players, "Mike Trout")

        pick1_data = {"player_id": mike_trout_id}

        pick1_response = client.post(
            f"/api/v1/draft/{league_id}/pick",
            json=pick1_data,
            headers=commissioner_headers,
        )
        assert pick1_response.status_code == 201

        pick1 = pick1_response.json()
        assert pick1["pick_number"] == 1
        assert pick1["player_id"] == mike_trout_id
        assert "team_id" in pick1
        assert "pick_time" in pick1

        # Step 3: Verify draft state after first pick
        draft_status_response = client.get(
            f"/api/v1/draft/{league_id}", headers=commissioner_headers
        )
        draft_status = draft_status_response.json()
        assert draft_status["current_pick"] == 2
        assert len(draft_status["picks"]) == 1
        assert draft_status["picks"][0]["player_id"] == mike_trout_id

        # Step 4: Second pick (user2's turn)
        aaron_judge_id = self._find_player_by_name(players, "Aaron Judge")

        pick2_data = {"player_id": aaron_judge_id}

        pick2_response = client.post(
            f"/api/v1/draft/{league_id}/pick", json=pick2_data, headers=user2_headers
        )
        assert pick2_response.status_code == 201

        pick2 = pick2_response.json()
        assert pick2["pick_number"] == 2
        assert pick2["player_id"] == aaron_judge_id

        # Step 5: Verify snake order (user2 should pick again in round 2)
        draft_status_response = client.get(
            f"/api/v1/draft/{league_id}", headers=commissioner_headers
        )
        draft_status = draft_status_response.json()
        assert draft_status["current_pick"] == 3

        # In snake draft with 2 teams: Pick 3 should be user2's turn again
        current_team_id = draft_status["current_team_id"]

        # Get team info to verify it's user2's team
        teams_response = client.get(
            f"/api/v1/leagues/{league_id}/teams", headers=commissioner_headers
        )
        teams = teams_response.json()
        user2_team = next(team for team in teams if team["team_id"] == current_team_id)

        # Verify it's user2's turn by making the pick
        third_player_id = self._find_available_player(
            players, [mike_trout_id, aaron_judge_id]
        )

        pick3_data = {"player_id": third_player_id}

        pick3_response = client.post(
            f"/api/v1/draft/{league_id}/pick", json=pick3_data, headers=user2_headers
        )
        assert pick3_response.status_code == 201

        # Step 6: Continue draft until completion
        # Pick 4 should be commissioner's turn
        fourth_player_id = self._find_available_player(
            players, [mike_trout_id, aaron_judge_id, third_player_id]
        )

        pick4_data = {"player_id": fourth_player_id}

        pick4_response = client.post(
            f"/api/v1/draft/{league_id}/pick",
            json=pick4_data,
            headers=commissioner_headers,
        )
        assert pick4_response.status_code == 201

        # Step 7: Verify final draft state
        final_draft_response = client.get(
            f"/api/v1/draft/{league_id}", headers=commissioner_headers
        )
        final_draft = final_draft_response.json()

        # With 2 teams and 2 rounds each, draft should be complete
        assert len(final_draft["picks"]) == 4
        assert final_draft["status"] == "completed"
        assert "completed_at" in final_draft

        # Verify player assignments to teams
        picks = final_draft["picks"]
        assert picks[0]["player_id"] == mike_trout_id  # Commissioner, Pick 1
        assert picks[1]["player_id"] == aaron_judge_id  # User2, Pick 2
        assert picks[2]["player_id"] == third_player_id  # User2, Pick 3 (snake)
        assert picks[3]["player_id"] == fourth_player_id  # Commissioner, Pick 4

    def test_draft_timer_functionality(self):
        """Test draft timer and auto-pick functionality"""
        if not client:
            pytest.fail("Application not implemented yet - TDD failing test")

        league_id, commissioner_headers, _ = self._setup_league_with_teams()

        # Start draft with short timer for testing
        draft_data = {"draft_type": "snake", "pick_timer": 5}  # 5 seconds for testing

        draft_response = client.post(
            f"/api/v1/draft/{league_id}", json=draft_data, headers=commissioner_headers
        )
        assert draft_response.status_code == 201

        # Wait for timer to expire
        time.sleep(6)

        # Check if auto-pick occurred
        draft_status_response = client.get(
            f"/api/v1/draft/{league_id}", headers=commissioner_headers
        )
        draft_status = draft_status_response.json()

        # Should have auto-picked and moved to next pick
        assert len(draft_status["picks"]) == 1
        assert draft_status["current_pick"] == 2

    def test_draft_validation_rules(self):
        """Test draft validation and error conditions"""
        if not client:
            pytest.fail("Application not implemented yet - TDD failing test")

        league_id, commissioner_headers, user2_headers = self._setup_league_with_teams()

        # Try to start draft as non-commissioner
        draft_data = {"draft_type": "snake", "pick_timer": 60}

        unauthorized_draft_response = client.post(
            f"/api/v1/draft/{league_id}", json=draft_data, headers=user2_headers
        )
        assert unauthorized_draft_response.status_code == 403

        # Start draft as commissioner
        draft_response = client.post(
            f"/api/v1/draft/{league_id}", json=draft_data, headers=commissioner_headers
        )
        assert draft_response.status_code == 201

        # Try to start draft again (should fail)
        duplicate_draft_response = client.post(
            f"/api/v1/draft/{league_id}", json=draft_data, headers=commissioner_headers
        )
        assert duplicate_draft_response.status_code == 400

        # Try to pick when it's not your turn
        players_response = client.get("/api/v1/sports/players?sport=mlb")
        players = players_response.json()
        player_id = players[0]["player_id"]

        wrong_turn_pick = {"player_id": player_id}

        wrong_turn_response = client.post(
            f"/api/v1/draft/{league_id}/pick",
            json=wrong_turn_pick,
            headers=user2_headers,  # User2 picking when it's commissioner's turn
        )
        assert wrong_turn_response.status_code == 400

        # Try to pick already drafted player
        valid_pick = client.post(
            f"/api/v1/draft/{league_id}/pick",
            json=wrong_turn_pick,
            headers=commissioner_headers,
        )
        assert valid_pick.status_code == 201

        # Now try to pick the same player again
        duplicate_pick_response = client.post(
            f"/api/v1/draft/{league_id}/pick",
            json=wrong_turn_pick,
            headers=user2_headers,
        )
        assert duplicate_pick_response.status_code == 400

    def test_draft_pause_and_resume(self):
        """Test draft pause and resume functionality"""
        if not client:
            pytest.fail("Application not implemented yet - TDD failing test")

        league_id, commissioner_headers, _ = self._setup_league_with_teams()

        # Start draft
        draft_data = {"draft_type": "snake", "pick_timer": 60}
        client.post(
            f"/api/v1/draft/{league_id}", json=draft_data, headers=commissioner_headers
        )

        # Pause draft
        pause_response = client.patch(
            f"/api/v1/draft/{league_id}",
            json={"action": "pause"},
            headers=commissioner_headers,
        )
        assert pause_response.status_code == 200

        draft_status = pause_response.json()
        assert draft_status["status"] == "paused"

        # Try to make pick while paused (should fail)
        players_response = client.get("/api/v1/sports/players?sport=mlb")
        player_id = players_response.json()[0]["player_id"]

        pick_while_paused = client.post(
            f"/api/v1/draft/{league_id}/pick",
            json={"player_id": player_id},
            headers=commissioner_headers,
        )
        assert pick_while_paused.status_code == 400

        # Resume draft
        resume_response = client.patch(
            f"/api/v1/draft/{league_id}",
            json={"action": "resume"},
            headers=commissioner_headers,
        )
        assert resume_response.status_code == 200

        draft_status = resume_response.json()
        assert draft_status["status"] == "active"

        # Now pick should work
        pick_after_resume = client.post(
            f"/api/v1/draft/{league_id}/pick",
            json={"player_id": player_id},
            headers=commissioner_headers,
        )
        assert pick_after_resume.status_code == 201

    def _setup_league_with_teams(self):
        """Helper method to set up a league with 2 teams"""
        # Create commissioner
        commissioner_data = {
            "email": "commissioner@test.com",
            "password": "password123",
            "name": "Test Commissioner",
        }
        commissioner_response = client.post(
            "/api/v1/auth/register", json=commissioner_data
        )
        commissioner_token = commissioner_response.json()["access_token"]
        commissioner_headers = {"Authorization": f"Bearer {commissioner_token}"}

        # Create league
        league_data = {
            "name": "Draft Test League",
            "sport": "mlb",
            "league_type": "head_to_head",
            "season": "2025",
            "max_teams": 8,
        }
        league_response = client.post(
            "/api/v1/leagues", json=league_data, headers=commissioner_headers
        )
        league = league_response.json()
        league_id = league["league_id"]

        # Create second user and join league
        user2_data = {
            "email": "user2@test.com",
            "password": "password123",
            "name": "Test User 2",
        }
        user2_response = client.post("/api/v1/auth/register", json=user2_data)
        user2_token = user2_response.json()["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        join_data = {"team_name": "Test Team 2", "invite_code": league["invite_code"]}
        client.post(
            f"/api/v1/leagues/{league_id}/join", json=join_data, headers=user2_headers
        )

        return league_id, commissioner_headers, user2_headers

    def _find_player_by_name(self, players, name):
        """Helper method to find player by name"""
        for player in players:
            if name.lower() in player["name"].lower():
                return player["player_id"]
        # Fallback to first player if name not found
        return players[0]["player_id"]

    def _find_available_player(self, players, taken_player_ids):
        """Helper method to find an available player"""
        for player in players:
            if player["player_id"] not in taken_player_ids:
                return player["player_id"]
        raise ValueError("No available players found")
