"""
Contract tests for GET /api/v1/sports/schedule endpoint.

These tests validate the API contract against the sports-data-api.yaml specification.
Tests must fail before implementation (TDD approach).
"""

import pytest
from fastapi.testclient import TestClient

from main import app


class TestSportsScheduleGetContract:
    """Contract tests for schedule endpoint."""

    # Removed setup_method - using authenticated_client fixture instead
    def test_get_schedule_returns_200_with_games_list(self, authenticated_client):
        """
        Contract Test: GET /api/v1/sports/schedule returns 200 with games list.

        This test will FAIL until the endpoint is implemented.
        """
        response = authenticated_client.get("/api/v1/sports/schedule")

        assert response.status_code == 200
        data = response.json()

        # Validate response structure matches contract
        assert "games" in data
        assert isinstance(data["games"], list)

    def test_get_schedule_with_date_filter_returns_filtered_results(self, authenticated_client):
        """
        Contract Test: GET /api/v1/sports/schedule?date=2024-01-01 returns games for date.

        This test will FAIL until date filtering is implemented.
        """
        response = authenticated_client.get("/api/v1/sports/schedule?date=2024-01-01")

        assert response.status_code == 200
        data = response.json()

        assert "games" in data

        # All returned games should be for the specified date
        for game in data["games"]:
            assert "2024-01-01" in game["game_date"]

    def test_get_schedule_response_includes_required_fields(self, authenticated_client):
        """
        Contract Test: Schedule response includes all required fields.

        This test will FAIL until proper response model is implemented.
        """
        response = authenticated_client.get("/api/v1/sports/schedule?limit=1")

        assert response.status_code == 200
        data = response.json()

        if data["games"]:
            game = data["games"][0]

            # Required fields per contract
            required_fields = [
                "game_id",
                "home_team",
                "away_team",
                "game_date",
                "game_time",
                "status",
                "week",
                "season",
            ]

            for field in required_fields:
                assert field in game, f"Missing required field: {field}"
