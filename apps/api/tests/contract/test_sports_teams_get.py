"""
Contract tests for GET /api/v1/sports/teams endpoint.

These tests validate the API contract against the sports-data-api.yaml specification.
Tests must fail before implementation (TDD approach).
"""

import pytest
from fastapi.testclient import TestClient

from main import app


class TestSportsTeamsGetContract:
    """Contract tests for teams endpoint."""

    # Removed setup_method - using authenticated_client fixture instead
    def test_get_teams_returns_200_with_teams_list(self, authenticated_client):
        """
        Contract Test: GET /api/v1/sports/teams returns 200 with teams list.

        This test will FAIL until the endpoint is implemented.
        """
        response = authenticated_client.get("/api/v1/sports/teams")

        assert response.status_code == 200
        data = response.json()

        # Validate response structure matches contract
        assert "teams" in data
        assert isinstance(data["teams"], list)

    def test_get_teams_with_sport_filter_returns_filtered_results(self, authenticated_client):
        """
        Contract Test: GET /api/v1/sports/teams?sport=NFL returns NFL teams only.

        This test will FAIL until sport filtering is implemented.
        """
        response = authenticated_client.get("/api/v1/sports/teams?sport=NFL")

        assert response.status_code == 200
        data = response.json()

        assert "teams" in data

        # All returned teams should be NFL teams
        for team in data["teams"]:
            assert team["sport"] == "NFL"

    def test_get_teams_response_includes_required_fields(self, authenticated_client):
        """
        Contract Test: Teams response includes all required fields.

        This test will FAIL until proper response model is implemented.
        """
        response = authenticated_client.get("/api/v1/sports/teams?limit=1")

        assert response.status_code == 200
        data = response.json()

        if data["teams"]:
            team = data["teams"][0]

            # Required fields per contract
            required_fields = [
                "team_id",
                "external_id",
                "name",
                "abbreviation",
                "city",
                "sport",
                "conference",
                "division",
            ]

            for field in required_fields:
                assert field in team, f"Missing required field: {field}"

    def test_get_teams_with_invalid_sport_returns_400(self, authenticated_client):
        """
        Contract Test: GET /api/v1/sports/teams?sport=INVALID returns 400.

        This test will FAIL until validation is implemented.
        """
        response = authenticated_client.get("/api/v1/sports/teams?sport=INVALID")

        assert response.status_code == 400
        data = response.json()

        assert "error" in data
        assert "message" in data
