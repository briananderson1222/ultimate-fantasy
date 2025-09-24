"""
Contract tests for GET /api/v1/sports/scores endpoint.

These tests validate the API contract against the sports-data-api.yaml specification.
Tests must fail before implementation (TDD approach).
"""

import pytest
from fastapi.testclient import TestClient

from main import app


class TestSportsScoresGetContract:
    """Contract tests for scores endpoint."""

    # Removed setup_method - using authenticated_client fixture instead
    def test_get_scores_returns_200_with_scores_list(self, authenticated_client):
        """
        Contract Test: GET /api/v1/sports/scores returns 200 with scores list.

        This test will FAIL until the endpoint is implemented.
        """
        response = authenticated_client.get("/api/v1/sports/scores")

        assert response.status_code == 200
        data = response.json()

        # Validate response structure matches contract
        assert "scores" in data
        assert isinstance(data["scores"], list)

    def test_get_scores_response_includes_required_fields(self, authenticated_client):
        """
        Contract Test: Scores response includes all required fields.

        This test will FAIL until proper response model is implemented.
        """
        response = authenticated_client.get("/api/v1/sports/scores?limit=1")

        assert response.status_code == 200
        data = response.json()

        if data["scores"]:
            score = data["scores"][0]

            # Required fields per contract
            required_fields = [
                "game_id",
                "home_team",
                "away_team",
                "home_score",
                "away_score",
                "quarter",
                "time_remaining",
                "status",
            ]

            for field in required_fields:
                assert field in score, f"Missing required field: {field}"
